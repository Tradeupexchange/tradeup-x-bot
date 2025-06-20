import React, { useState, useEffect } from 'react';
import { Play, Square, RefreshCw, AlertCircle, CheckCircle, MessageSquare, Reply, Settings, Clock, Target, Eye, Check, X, Calendar, Plus, Trash2, Edit2, RotateCcw } from 'lucide-react';
import { useApi, useNextRefreshTime, apiCall } from '../hooks/useApi';

interface BotJob {
  id: string;
  name: string;
  type: 'posting' | 'replying';
  status: 'running' | 'stopped' | 'paused';
  settings: any;
  createdAt?: string;
  lastRun?: string;
  nextRun?: string;
  stats: {
    postsToday: number;
    repliesToday: number;
    successRate: number;
  };
}

interface BotStatus {
  running: boolean;
  uptime: string | null;
  lastRun: string | null;
  stats: {
    postsToday: number;
    repliesToday: number;
    successRate: number;
  };
  jobs: BotJob[];
  timestamp: string;
}

interface GeneratedPost {
  id: string;
  content: string;
  topic: string;
  approved: boolean | null; // null = pending, true = approved, false = rejected
  scheduledTime?: string;
  engagement_score?: number;
  hashtags?: string[];
  mentions_tradeup?: boolean;
}

interface JobSettings {
  postsPerDay: number;
  topics: string[];
  postingTimeStart: string;
  postingTimeEnd: string;
  contentTypes: {
    cardPulls: boolean;
    deckBuilding: boolean;
    marketAnalysis: boolean;
    tournaments: boolean;
  };
}

const BotControl: React.FC = () => {
  // Use the centralized useApi hook - it automatically handles 20-minute intervals!
  const { data: status, loading, error, lastFetch, refetch } = useApi<BotStatus>('/api/bot-status');
  
  const [jobs, setJobs] = useState<BotJob[]>([]);
  const [jobCounter, setJobCounter] = useState(1);
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [showScheduler, setShowScheduler] = useState(false);
  const [showPostApproval, setShowPostApproval] = useState(false);
  const [generatedPosts, setGeneratedPosts] = useState<GeneratedPost[]>([]);
  const [currentJobSettings, setCurrentJobSettings] = useState<JobSettings | null>(null);
  const [editingJobId, setEditingJobId] = useState<string | null>(null);
  const [editingJobName, setEditingJobName] = useState('');

  // Update jobs when status changes
  useEffect(() => {
    if (status?.jobs && Array.isArray(status.jobs)) {
      setJobs(status.jobs);
      // Update job counter based on existing jobs
      const maxJobNumber = status.jobs.reduce((max, job) => {
        const match = job.name?.match(/^Job #(\d+)$/);
        if (match) {
          return Math.max(max, parseInt(match[1]));
        }
        return max;
      }, 0);
      setJobCounter(maxJobNumber + 1);
      console.log('Updated jobs from API:', status.jobs);
    }
  }, [status]);

  const handleJobAction = async (jobId: string, action: 'start' | 'stop' | 'pause') => {
    try {
      setActionLoading(`${jobId}-${action}`);
      console.log(`Performing ${action} on job ${jobId}`);
      
      const result = await apiCall(`/api/bot-job/${jobId}/${action}`, { 
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        }
      });
      
      console.log(`${action} result:`, result);
      
      // Wait a moment then refetch to get updated status
      setTimeout(() => {
        refetch();
        setActionLoading(null);
      }, 1000);
    } catch (error) {
      console.error(`Error ${action}ing job:`, error);
      alert(`Failed to ${action} job: ${error instanceof Error ? error.message : 'Unknown error'}`);
      setActionLoading(null);
    }
  };

  const handleJobRename = async (jobId: string, newName: string) => {
    try {
      const result = await apiCall(`/api/bot-job/${jobId}/rename`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ name: newName })
      });
      
      if (result.success) {
        setJobs(prev => prev.map(job => 
          job.id === jobId ? { ...job, name: newName } : job
        ));
        setEditingJobId(null);
        setEditingJobName('');
      }
    } catch (error) {
      console.error('Error renaming job:', error);
      alert(`Failed to rename job: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  };

  const generateScheduledTimes = (count: number, startTime: string, endTime: string): string[] => {
    const times: string[] = [];
    const [startHour, startMin] = startTime.split(':').map(Number);
    const [endHour, endMin] = endTime.split(':').map(Number);
    
    const startMinutes = startHour * 60 + startMin;
    const endMinutes = endHour * 60 + endMin;
    const totalMinutes = endMinutes - startMinutes;
    const interval = Math.floor(totalMinutes / count);
    
    for (let i = 0; i < count; i++) {
      const postTime = startMinutes + (interval * i);
      const hour = Math.floor(postTime / 60);
      const minute = postTime % 60;
      times.push(`${hour.toString().padStart(2, '0')}:${minute.toString().padStart(2, '0')}`);
    }
    
    return times;
  };

  const createJobWithApproval = async (jobSettings: JobSettings, jobName: string) => {
    try {
      setActionLoading('generate-posts');
      console.log('🧪 Creating job with approval workflow...');

      // Use provided name or generate automatic name
      const finalJobName = jobName.trim() || `Job #${jobCounter}`;
      if (!jobName.trim()) {
        setJobCounter(prev => prev + 1);
      }

      // Step 1: Generate posts for approval
      console.log('📝 Generating posts for approval...');
      const posts: GeneratedPost[] = [];
      
      for (let i = 0; i < jobSettings.postsPerDay; i++) {
        const randomTopic = jobSettings.topics[Math.floor(Math.random() * jobSettings.topics.length)];
        
        const contentResult = await apiCall('/api/generate-content', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            topic: randomTopic,
            count: 1
          })
        });

        if (contentResult.success && contentResult.content) {
          posts.push({
            id: `post-${Date.now()}-${i}`,
            content: contentResult.content.content || contentResult.content,
            topic: randomTopic,
            approved: null,
            engagement_score: contentResult.content.engagement_score,
            hashtags: contentResult.content.hashtags,
            mentions_tradeup: contentResult.content.mentions_tradeup
          });
        }
      }

      // Generate scheduled times
      const scheduledTimes = generateScheduledTimes(
        jobSettings.postsPerDay,
        jobSettings.postingTimeStart,
        jobSettings.postingTimeEnd
      );

      // Assign scheduled times to posts
      posts.forEach((post, index) => {
        post.scheduledTime = scheduledTimes[index];
      });

      setGeneratedPosts(posts);
      setCurrentJobSettings({ ...jobSettings, name: finalJobName } as any);
      setShowScheduler(false);
      setShowPostApproval(true);

    } catch (error) {
      console.error('❌ Post generation failed:', error);
      alert(`Failed to generate posts: ${error instanceof Error ? error.message : 'Unknown error'}`);
    } finally {
      setActionLoading(null);
    }
  };

  const approvePost = (postId: string) => {
    setGeneratedPosts(prev => 
      prev.map(post => 
        post.id === postId ? { ...post, approved: true } : post
      )
    );
  };

  const rejectPost = async (postId: string) => {
    // Automatically regenerate when rejecting
    await regeneratePost(postId);
  };

  const regeneratePost = async (postId: string) => {
    try {
      setActionLoading(`regenerate-${postId}`);
      const post = generatedPosts.find(p => p.id === postId);
      if (!post) return;

      const contentResult = await apiCall('/api/generate-content', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          topic: post.topic,
          count: 1
        })
      });

      if (contentResult.success && contentResult.content) {
        setGeneratedPosts(prev => 
          prev.map(p => 
            p.id === postId 
              ? {
                  ...p,
                  content: contentResult.content.content || contentResult.content,
                  approved: null,
                  engagement_score: contentResult.content.engagement_score,
                  hashtags: contentResult.content.hashtags,
                  mentions_tradeup: contentResult.content.mentions_tradeup
                }
              : p
          )
        );
      }
    } catch (error) {
      console.error('❌ Post regeneration failed:', error);
      alert(`Failed to regenerate post: ${error instanceof Error ? error.message : 'Unknown error'}`);
    } finally {
      setActionLoading(null);
    }
  };

  const scheduleApprovedPosts = async () => {
    try {
      setActionLoading('schedule');
      const approvedPosts = generatedPosts.filter(post => post.approved === true);
      
      if (approvedPosts.length === 0) {
        alert('Please approve at least one post before scheduling.');
        return;
      }

      console.log('📅 Scheduling approved posts...', approvedPosts);

      // Create the actual job with approved posts
      const result = await apiCall('/api/bot-job/create', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          type: 'posting',
          name: (currentJobSettings as any)?.name || 'Untitled Job',
          settings: {
            ...currentJobSettings,
            approvedPosts: approvedPosts,
            autoPost: true
          }
        })
      });

      if (result.success) {
        alert(`Successfully scheduled ${approvedPosts.length} posts!`);
        setShowPostApproval(false);
        setGeneratedPosts([]);
        refetch(); // Refresh the jobs list
      }

    } catch (error) {
      console.error('❌ Scheduling failed:', error);
      alert(`Failed to schedule posts: ${error instanceof Error ? error.message : 'Unknown error'}`);
    } finally {
      setActionLoading(null);
    }
  };

  const createNewJob = async (type: 'posting' | 'replying', settings: any, jobName: string) => {
    try {
      setActionLoading('create');
      
      // Use provided name or generate automatic name
      const finalJobName = jobName.trim() || `Job #${jobCounter}`;
      if (!jobName.trim()) {
        setJobCounter(prev => prev + 1);
      }
      
      console.log('Creating new job:', { type, settings, name: finalJobName });
      
      const result = await apiCall('/api/bot-job/create', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ type, settings, name: finalJobName })
      });
      
      console.log('Job creation result:', result);
      
      // Refetch status to get updated jobs list
      refetch();
      setActionLoading(null);
      setShowScheduler(false);
      
      alert(`${type} job created successfully!`);
    } catch (error) {
      console.error('Error creating job:', error);
      alert(`Failed to create job: ${error instanceof Error ? error.message : 'Unknown error'}`);
      setActionLoading(null);
    }
  };

  if (loading && !status) {
    return (
      <div className="bg-white rounded-xl p-6 shadow-sm">
        <div className="animate-pulse space-y-4">
          <div className="h-6 bg-gray-200 rounded w-1/3"></div>
          <div className="space-y-3">
            <div className="h-4 bg-gray-200 rounded"></div>
            <div className="h-4 bg-gray-200 rounded w-5/6"></div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Overall Bot Status */}
      <div className="bg-white rounded-xl p-6 shadow-sm">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center space-x-4">
            <div className="p-3">
              <img 
                src="/pokeball.png" 
                alt="Pokeball" 
                className="h-6 w-6"
                onError={(e) => {
                  // Fallback to checkmark icon if pokeball.png doesn't exist
                  const target = e.target as HTMLImageElement;
                  target.style.display = 'none';
                  target.nextElementSibling?.classList.remove('hidden');
                }}
              />
              <CheckCircle className="h-6 w-6 text-red-600 hidden" />
            </div>
            <div>
              <h3 className="text-xl font-semibold text-gray-900">
                Automated Posting
              </h3>
              <p className="text-sm text-gray-600">
                Generate, approve, and schedule posts
              </p>
            </div>
          </div>
          
          <div className="flex space-x-3">
            <button
              onClick={() => setShowScheduler(true)}
              disabled={actionLoading === 'create'}
              className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors duration-200"
            >
              {actionLoading === 'create' ? (
                <RefreshCw className="h-4 w-4 animate-spin" />
              ) : (
                <Calendar className="h-4 w-4" />
              )}
              <span>{actionLoading === 'create' ? 'Creating...' : 'New Job'}</span>
            </button>

            {generatedPosts.length > 0 && (
              <button
                onClick={() => setShowPostApproval(true)}
                className="flex items-center space-x-2 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors duration-200"
              >
                <Eye className="h-4 w-4" />
                <span>Review Posts ({generatedPosts.filter(p => p.approved === null).length})</span>
              </button>
            )}

            {loading && (
              <div className="flex items-center space-x-2 px-4 py-2 bg-gray-100 text-gray-600 rounded-lg">
                <RefreshCw className="h-4 w-4 animate-spin" />
                <span>Updating...</span>
              </div>
            )}
          </div>
        </div>

        {/* Error display */}
        {error && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-sm text-red-700">⚠️ {error}</p>
          </div>
        )}
      </div>

      {/* Active Jobs */}
      <div className="bg-white rounded-xl p-6 shadow-sm">
        <h4 className="text-lg font-semibold text-gray-900 mb-4">Active Jobs</h4>
        
        {jobs.length === 0 ? (
          <div className="text-center py-8">
            <AlertCircle className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <p className="text-gray-500 mb-4">No active jobs running</p>
            <p className="text-sm text-gray-400">Create a new job to get started with automated posting or replying</p>
          </div>
        ) : (
          <div className="space-y-4">
            {jobs.map((job) => (
              <JobCard
                key={job.id}
                job={job}
                onAction={handleJobAction}
                onRename={handleJobRename}
                actionLoading={actionLoading}
                editingJobId={editingJobId}
                editingJobName={editingJobName}
                setEditingJobId={setEditingJobId}
                setEditingJobName={setEditingJobName}
              />
            ))}
          </div>
        )}
      </div>

      {/* Enhanced Job Scheduler Modal */}
      {showScheduler && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-[60]">
          <EnhancedJobScheduler
            onClose={() => setShowScheduler(false)}
            onCreateJob={createNewJob}
            onCreateJobWithApproval={createJobWithApproval}
            loading={actionLoading === 'create' || actionLoading === 'generate-posts'}
          />
        </div>
      )}

      {/* Post Approval Modal */}
      {showPostApproval && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-[60]">
          <PostApprovalModal
            posts={generatedPosts}
            onApprove={approvePost}
            onReject={rejectPost}
            onRegenerate={regeneratePost}
            onSchedule={scheduleApprovedPosts}
            onClose={() => setShowPostApproval(false)}
            loading={actionLoading}
          />
        </div>
      )}
    </div>
  );
};

// Enhanced Job Scheduler with post approval option
interface EnhancedJobSchedulerProps {
  onClose: () => void;
  onCreateJob: (type: 'posting' | 'replying', settings: any, jobName: string) => void;
  onCreateJobWithApproval: (settings: JobSettings, jobName: string) => void;
  loading: boolean;
}

const EnhancedJobScheduler: React.FC<EnhancedJobSchedulerProps> = ({ 
  onClose, 
  onCreateJob, 
  onCreateJobWithApproval, 
  loading 
}) => {
  const [jobType, setJobType] = useState<'posting' | 'replying'>('posting');
  const [useApprovalWorkflow, setUseApprovalWorkflow] = useState(true);
  const [newTopic, setNewTopic] = useState('');
  const [jobName, setJobName] = useState('');
  
  const [settings, setSettings] = useState({
    // Posting settings
    postsPerDay: 5,
    topics: ['Pokemon TCG'],
    postingTimeStart: '09:00',
    postingTimeEnd: '17:00',
    contentTypes: {
      cardPulls: true,
      deckBuilding: true,
      marketAnalysis: true,
      tournaments: false
    },
    
    // Reply settings
    keywords: ['Pokemon', 'TCG', 'Charizard', 'Pikachu'],
    maxRepliesPerHour: 10,
    replyTypes: {
      helpful: true,
      engaging: true,
      promotional: false
    }
  });

  const addTopic = () => {
    if (newTopic.trim() && !settings.topics.includes(newTopic.trim())) {
      setSettings(prev => ({
        ...prev,
        topics: [...prev.topics, newTopic.trim()]
      }));
      setNewTopic('');
    }
  };

  const removeTopic = (topic: string) => {
    setSettings(prev => ({
      ...prev,
      topics: prev.topics.filter(t => t !== topic)
    }));
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    try {
      if (jobType === 'posting' && useApprovalWorkflow) {
        // Use the enhanced workflow with post approval
        const jobSettings: JobSettings = {
          postsPerDay: settings.postsPerDay,
          topics: settings.topics,
          postingTimeStart: settings.postingTimeStart,
          postingTimeEnd: settings.postingTimeEnd,
          contentTypes: settings.contentTypes
        };
        onCreateJobWithApproval(jobSettings, jobName);
      } else {
        // Use the original workflow
        onCreateJob(jobType, settings, jobName);
      }
    } catch (error) {
      console.error('Error in form submission:', error);
    }
  };

  return (
    <div className="bg-white rounded-xl max-w-3xl w-full max-h-[90vh] overflow-y-auto">
      <div className="p-6 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <h3 className="text-xl font-semibold text-gray-900">Create New Bot Job</h3>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
            <X className="h-5 w-5" />
          </button>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="p-6 space-y-6">
        {/* Job Name */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Job Name (optional)
          </label>
          <input
            type="text"
            value={jobName}
            onChange={(e) => setJobName(e.target.value)}
            placeholder="Enter a name for this job or leave empty for auto-generation"
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
          />
        </div>

        {/* Job Type Selection */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-3">
            What should the bot do?
          </label>
          <div className="grid grid-cols-2 gap-4">
            <button
              type="button"
              onClick={() => setJobType('posting')}
              className={`p-4 rounded-lg border-2 transition-all duration-200 ${
                jobType === 'posting'
                  ? 'border-blue-500 bg-blue-50'
                  : 'border-gray-200 hover:border-gray-300'
              }`}
            >
              <MessageSquare className="h-6 w-6 text-blue-600 mx-auto mb-2" />
              <p className="font-medium">Post Original Content</p>
              <p className="text-xs text-gray-600 mt-1">
                Create and publish Pokemon TCG posts
              </p>
            </button>
            
            <button
              type="button"
              onClick={() => setJobType('replying')}
              className={`p-4 rounded-lg border-2 transition-all duration-200 ${
                jobType === 'replying'
                  ? 'border-green-500 bg-green-50'
                  : 'border-gray-200 hover:border-gray-300'
              }`}
            >
              <Reply className="h-6 w-6 text-green-600 mx-auto mb-2" />
              <p className="font-medium">Reply to Others</p>
              <p className="text-xs text-gray-600 mt-1">
                Engage with other Pokemon TCG posts
              </p>
            </button>
          </div>
        </div>

        {/* Approval Workflow Toggle (only for posting) */}
        {jobType === 'posting' && (
          <div className="bg-blue-50 rounded-lg p-4">
            <label className="flex items-center space-x-3">
              <input
                type="checkbox"
                checked={useApprovalWorkflow}
                onChange={(e) => setUseApprovalWorkflow(e.target.checked)}
                className="w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500"
              />
              <div>
                <span className="text-sm font-medium text-blue-900">
                  Use Post Approval Workflow
                </span>
                <p className="text-xs text-blue-700">
                  Generate posts for review before scheduling (Recommended)
                </p>
              </div>
            </label>
          </div>
        )}

        {/* Job-specific settings */}
        {jobType === 'posting' ? (
          <EnhancedPostingSettings 
            settings={settings} 
            onChange={setSettings}
            newTopic={newTopic}
            setNewTopic={setNewTopic}
            addTopic={addTopic}
            removeTopic={removeTopic}
          />
        ) : (
          <ReplyingSettings settings={settings} onChange={setSettings} />
        )}

        {/* Submit buttons */}
        <div className="flex space-x-4 pt-4 border-t border-gray-200">
          <button
            type="submit"
            disabled={loading}
            className="flex items-center space-x-2 px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors duration-200"
          >
            {loading ? (
              <RefreshCw className="h-4 w-4 animate-spin" />
            ) : useApprovalWorkflow && jobType === 'posting' ? (
              <Eye className="h-4 w-4" />
            ) : (
              <Play className="h-4 w-4" />
            )}
            <span>
              {loading ? 'Processing...' : 
               useApprovalWorkflow && jobType === 'posting' ? 'Generate for Approval' : 'Start Job'
              }
            </span>
          </button>
          <button
            type="button"
            onClick={onClose}
            className="px-6 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors duration-200"
          >
            Cancel
          </button>
        </div>
      </form>
    </div>
  );
};

// Enhanced Posting Settings with topics management
const EnhancedPostingSettings: React.FC<{
  settings: any;
  onChange: (settings: any) => void;
  newTopic: string;
  setNewTopic: (topic: string) => void;
  addTopic: () => void;
  removeTopic: (topic: string) => void;
}> = ({ settings, onChange, newTopic, setNewTopic, addTopic, removeTopic }) => {
  return (
    <div className="space-y-6">
      {/* Posts per day */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Posts per day: {settings.postsPerDay}
        </label>
        <input
          type="range"
          min="1"
          max="20"
          value={settings.postsPerDay}
          onChange={(e) => onChange({
            ...settings,
            postsPerDay: parseInt(e.target.value)
          })}
          className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
        />
        <div className="flex justify-between text-xs text-gray-500 mt-1">
          <span>1</span>
          <span>10</span>
          <span>20</span>
        </div>
      </div>

      {/* Posting time range */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Posting Hours
        </label>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="text-xs text-gray-500">Start Time</label>
            <input
              type="time"
              value={settings.postingTimeStart}
              onChange={(e) => onChange({
                ...settings,
                postingTimeStart: e.target.value
              })}
              className="w-full mt-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="text-xs text-gray-500">End Time</label>
            <input
              type="time"
              value={settings.postingTimeEnd}
              onChange={(e) => onChange({
                ...settings,
                postingTimeEnd: e.target.value
              })}
              className="w-full mt-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>
      </div>

      {/* Topics */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">Topics</label>
        <div className="flex gap-2 mb-3">
          <input
            type="text"
            value={newTopic}
            onChange={(e) => setNewTopic(e.target.value)}
            placeholder="Add new topic..."
            className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            onKeyPress={(e) => e.key === 'Enter' && addTopic()}
          />
          <button
            type="button"
            onClick={addTopic}
            className="px-3 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            <Plus className="h-4 w-4" />
          </button>
        </div>
        <div className="flex flex-wrap gap-2">
          {settings.topics.map((topic: string) => (
            <span
              key={topic}
              className="bg-blue-100 text-blue-800 px-3 py-1 rounded-lg text-sm flex items-center gap-2"
            >
              {topic}
              <button
                type="button"
                onClick={() => removeTopic(topic)}
                className="text-blue-600 hover:text-blue-800"
              >
                <X className="h-3 w-3" />
              </button>
            </span>
          ))}
        </div>
      </div>

      {/* Content Types */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-3">
          Content Types to Post
        </label>
        <div className="grid grid-cols-2 gap-3">
          {Object.entries(settings.contentTypes).map(([type, enabled]) => (
            <label key={type} className="flex items-center justify-between">
              <span className="text-sm text-gray-700 capitalize">
                {type.replace(/([A-Z])/g, ' $1').trim()}
              </span>
              <input
                type="checkbox"
                checked={enabled as boolean}
                onChange={(e) => onChange({
                  ...settings,
                  contentTypes: {
                    ...settings.contentTypes,
                    [type]: e.target.checked
                  }
                })}
                className="w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500"
              />
            </label>
          ))}
        </div>
      </div>
    </div>
  );
};

// Post Approval Modal Component
interface PostApprovalModalProps {
  posts: GeneratedPost[];
  onApprove: (postId: string) => void;
  onReject: (postId: string) => void;
  onRegenerate: (postId: string) => void;
  onSchedule: () => void;
  onClose: () => void;
  loading: string | null;
}

const PostApprovalModal: React.FC<PostApprovalModalProps> = ({
  posts,
  onApprove,
  onReject,
  onRegenerate,
  onSchedule,
  onClose,
  loading
}) => {
  const approvedCount = posts.filter(p => p.approved === true).length;
  const rejectedCount = posts.filter(p => p.approved === false).length;
  const pendingCount = posts.filter(p => p.approved === null).length;

  return (
    <div className="bg-white rounded-xl max-w-5xl w-full max-h-[90vh] overflow-y-auto shadow-2xl">
      <div className="p-6 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <h3 className="text-xl font-semibold text-gray-900">Review & Approve Posts</h3>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
            <X className="h-5 w-5" />
          </button>
        </div>
          
          {/* Stats bar */}
          <div className="mt-4 grid grid-cols-4 gap-4 text-sm">
            <div className="bg-blue-50 rounded-lg p-3 text-center">
              <div className="font-semibold text-blue-900">{posts.length}</div>
              <div className="text-blue-700">Total</div>
            </div>
            <div className="bg-green-50 rounded-lg p-3 text-center">
              <div className="font-semibold text-green-900">{approvedCount}</div>
              <div className="text-green-700">Approved</div>
            </div>
            <div className="bg-red-50 rounded-lg p-3 text-center">
              <div className="font-semibold text-red-900">{rejectedCount}</div>
              <div className="text-red-700">Rejected</div>
            </div>
            <div className="bg-yellow-50 rounded-lg p-3 text-center">
              <div className="font-semibold text-yellow-900">{pendingCount}</div>
              <div className="text-yellow-700">Pending</div>
            </div>
          </div>
        </div>

        {/* Posts list */}
        <div className="p-6 space-y-4 max-h-96 overflow-y-auto">
          {posts.map((post) => (
            <div
              key={post.id}
              className={`p-4 border-2 rounded-lg transition-all duration-200 ${
                post.approved === true
                  ? 'border-green-200 bg-green-50'
                  : post.approved === false
                  ? 'border-red-200 bg-red-50'
                  : 'border-gray-200 bg-white hover:border-gray-300'
              }`}
            >
              <div className="flex items-start justify-between">
                <div className="flex-1 mr-4">
                  {/* Post metadata */}
                  <div className="flex items-center gap-2 mb-2">
                    <span className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded-full">
                      {post.topic}
                    </span>
                    <span className="text-xs text-gray-500 flex items-center gap-1">
                      <Clock className="h-3 w-3" />
                      {post.scheduledTime}
                    </span>
                    {post.mentions_tradeup && (
                      <span className="text-xs bg-purple-100 text-purple-800 px-2 py-1 rounded-full">
                        TradeUp Mention
                      </span>
                    )}
                  </div>

                  {/* Post content */}
                  <p className="text-gray-900 mb-3 leading-relaxed">{post.content}</p>

                  {/* Hashtags */}
                  {post.hashtags && post.hashtags.length > 0 && (
                    <div className="flex gap-1 flex-wrap">
                      {post.hashtags.map((tag, i) => (
                        <span key={i} className="text-xs text-blue-600 bg-blue-50 px-2 py-1 rounded">
                          {tag}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
                
                {/* Action buttons */}
                <div className="flex gap-2 flex-shrink-0">
                  <button
                    onClick={() => onApprove(post.id)}
                    disabled={post.approved === true}
                    className={`p-2 rounded-lg transition-all duration-200 ${
                      post.approved === true
                        ? 'bg-green-600 text-white cursor-default'
                        : 'bg-green-100 text-green-800 hover:bg-green-200 hover:scale-105'
                    }`}
                    title="Approve post"
                  >
                    <Check className="h-4 w-4" />
                  </button>
                  
                  <button
                    onClick={() => onReject(post.id)}
                    disabled={loading === `regenerate-${post.id}`}
                    className="p-2 rounded-lg bg-red-100 text-red-800 hover:bg-red-200 hover:scale-105 transition-all duration-200 disabled:opacity-50"
                    title="Reject and regenerate post"
                  >
                    {loading === `regenerate-${post.id}` ? (
                      <RefreshCw className="h-4 w-4 animate-spin" />
                    ) : (
                      <X className="h-4 w-4" />
                    )}
                  </button>
                </div>
              </div>

              {/* Approval status indicator */}
              {post.approved !== null && (
                <div className={`mt-3 pt-3 border-t ${
                  post.approved ? 'border-green-200' : 'border-red-200'
                }`}>
                  <span className={`text-xs font-medium ${
                    post.approved ? 'text-green-800' : 'text-red-800'
                  }`}>
                    {post.approved 
                      ? '✓ Approved for scheduling' 
                      : loading === `regenerate-${post.id}`
                      ? '🔄 Regenerating content...'
                      : '✗ Regenerating new version...'
                    }
                  </span>
                </div>
              )}
            </div>
          ))}
        </div>

        {/* Action buttons */}
        <div className="p-6 border-t border-gray-200 bg-gray-50">
          <div className="flex gap-4">
            <button
              onClick={onSchedule}
              disabled={loading === 'schedule' || approvedCount === 0}
              className="flex-1 flex items-center justify-center space-x-2 px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200"
            >
              {loading === 'schedule' ? (
                <RefreshCw className="h-4 w-4 animate-spin" />
              ) : (
                <Calendar className="h-4 w-4" />
              )}
              <span>
                {loading === 'schedule' ? 'Scheduling...' : `Schedule ${approvedCount} Approved Posts`}
              </span>
            </button>
            <button
              onClick={onClose}
              className="px-6 py-3 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-100 transition-colors duration-200"
            >
              Cancel
            </button>
          </div>
          
          {approvedCount === 0 && (
            <p className="text-sm text-gray-500 text-center mt-3">
              Please approve at least one post before scheduling
            </p>
          )}
        </div>
      </div>
    </div>
  );
};

// Job Card Component
interface JobCardProps {
  job: BotJob;
  onAction: (jobId: string, action: 'start' | 'stop' | 'pause') => void;
  onRename: (jobId: string, newName: string) => void;
  actionLoading: string | null;
  editingJobId: string | null;
  editingJobName: string;
  setEditingJobId: (id: string | null) => void;
  setEditingJobName: (name: string) => void;
}

const JobCard: React.FC<JobCardProps> = ({ 
  job, 
  onAction, 
  onRename,
  actionLoading, 
  editingJobId,
  editingJobName,
  setEditingJobId,
  setEditingJobName
}) => {
  const isRunning = job.status === 'running';
  const isLoading = actionLoading?.startsWith(job.id);
  const isEditing = editingJobId === job.id;

  const handleStartEdit = () => {
    setEditingJobId(job.id);
    setEditingJobName(job.name || `${job.type} Job`);
  };

  const handleSaveEdit = () => {
    if (editingJobName.trim()) {
      onRename(job.id, editingJobName.trim());
    } else {
      setEditingJobId(null);
      setEditingJobName('');
    }
  };

  const handleCancelEdit = () => {
    setEditingJobId(null);
    setEditingJobName('');
  };

  return (
    <div className="border border-gray-200 rounded-lg p-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <div className={`p-2 rounded-lg ${
            job.type === 'posting' ? 'bg-blue-100' : 'bg-green-100'
          }`}>
            {job.type === 'posting' ? (
              <MessageSquare className="h-5 w-5 text-blue-600" />
            ) : (
              <Reply className="h-5 w-5 text-green-600" />
            )}
          </div>
          
          <div className="flex-1">
            {isEditing ? (
              <div className="flex items-center space-x-2">
                <input
                  type="text"
                  value={editingJobName}
                  onChange={(e) => setEditingJobName(e.target.value)}
                  className="px-2 py-1 border border-gray-300 rounded text-sm font-medium"
                  onKeyPress={(e) => e.key === 'Enter' && handleSaveEdit()}
                  autoFocus
                />
                <button
                  onClick={handleSaveEdit}
                  className="p-1 text-green-600 hover:text-green-800"
                >
                  <Check className="h-4 w-4" />
                </button>
                <button
                  onClick={handleCancelEdit}
                  className="p-1 text-red-600 hover:text-red-800"
                >
                  <X className="h-4 w-4" />
                </button>
              </div>
            ) : (
              <div className="flex items-center space-x-2">
                <h5 className="font-medium text-gray-900">
                  {job.name || `${job.type.charAt(0).toUpperCase() + job.type.slice(1)} Job`}
                </h5>
                <button
                  onClick={handleStartEdit}
                  className="p-1 text-gray-400 hover:text-gray-600"
                >
                  <Edit2 className="h-3 w-3" />
                </button>
              </div>
            )}
            <p className="text-sm text-gray-600">
              {job.type === 'posting' 
                ? `${job.settings?.postsPerDay || 12} posts/day` 
                : `Monitoring ${job.settings?.keywords?.length || 0} keywords`
              }
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-2">
          <div className={`px-2 py-1 rounded-full text-xs font-medium ${
            isRunning 
              ? 'bg-green-100 text-green-800' 
              : job.status === 'paused'
              ? 'bg-yellow-100 text-yellow-800'
              : 'bg-gray-100 text-gray-800'
          }`}>
            {job.status}
          </div>
          
          {isRunning ? (
            <button
              onClick={() => onAction(job.id, 'stop')}
              disabled={isLoading}
              className="flex items-center space-x-1 px-3 py-1 bg-red-600 text-white rounded hover:bg-red-700 disabled:opacity-50 transition-colors duration-200"
            >
              {isLoading ? (
                <RefreshCw className="h-3 w-3 animate-spin" />
              ) : (
                <Square className="h-3 w-3" />
              )}
              <span className="text-xs">Stop</span>
            </button>
          ) : (
            <button
              onClick={() => onAction(job.id, 'start')}
              disabled={isLoading}
              className="flex items-center space-x-1 px-3 py-1 bg-green-600 text-white rounded hover:bg-green-700 disabled:opacity-50 transition-colors duration-200"
            >
              {isLoading ? (
                <RefreshCw className="h-3 w-3 animate-spin" />
              ) : (
                <Play className="h-3 w-3" />
              )}
              <span className="text-xs">Start</span>
            </button>
          )}
        </div>
      </div>

      {/* Job Details */}
      <div className="mt-4 pt-4 border-t border-gray-100">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
          <div>
            <span className="text-gray-500">Last Run:</span>
            <p className="font-medium">
              {job.lastRun ? new Date(job.lastRun).toLocaleTimeString() : 'Never'}
            </p>
          </div>
          <div>
            <span className="text-gray-500">Next Run:</span>
            <p className="font-medium">
              {job.nextRun ? new Date(job.nextRun).toLocaleTimeString() : 'Not scheduled'}
            </p>
          </div>
          <div>
            <span className="text-gray-500">Today's Count:</span>
            <p className="font-medium">
              {job.type === 'posting' ? job.stats.postsToday : job.stats.repliesToday}
            </p>
          </div>
          <div>
            <span className="text-gray-500">Success Rate:</span>
            <p className="font-medium">{job.stats.successRate}%</p>
          </div>
        </div>
      </div>
    </div>
  );
};

// Replying Settings Component
const ReplyingSettings: React.FC<{ settings: any; onChange: (settings: any) => void }> = ({
  settings,
  onChange
}) => {
  const [newKeyword, setNewKeyword] = useState('');

  const addKeyword = () => {
    if (newKeyword.trim() && !settings.keywords.includes(newKeyword.trim())) {
      onChange({
        ...settings,
        keywords: [...settings.keywords, newKeyword.trim()]
      });
      setNewKeyword('');
    }
  };

  const removeKeyword = (keyword: string) => {
    onChange({
      ...settings,
      keywords: settings.keywords.filter((k: string) => k !== keyword)
    });
  };

  return (
    <div className="space-y-4">
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Keywords to Monitor
        </label>
        <div className="flex flex-wrap gap-2 mb-3">
          {settings.keywords.map((keyword: string, index: number) => (
            <span
              key={index}
              className="inline-flex items-center px-3 py-1 rounded-full text-sm bg-blue-50 text-blue-700"
            >
              {keyword}
              <button
                type="button"
                onClick={() => removeKeyword(keyword)}
                className="ml-2 hover:text-red-500"
              >
                ×
              </button>
            </span>
          ))}
        </div>
        <div className="flex space-x-2">
          <input
            type="text"
            value={newKeyword}
            onChange={(e) => setNewKeyword(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && addKeyword()}
            placeholder="Add keyword..."
            className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
          />
          <button
            type="button"
            onClick={addKeyword}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            Add
          </button>
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Max Replies per Hour: {settings.maxRepliesPerHour}
        </label>
        <input
          type="range"
          min="1"
          max="30"
          value={settings.maxRepliesPerHour}
          onChange={(e) => onChange({
            ...settings,
            maxRepliesPerHour: parseInt(e.target.value)
          })}
          className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
        />
        <div className="flex justify-between text-xs text-gray-500 mt-1">
          <span>1</span>
          <span>15</span>
          <span>30</span>
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-3">
          Reply Types
        </label>
        <div className="space-y-2">
          {Object.entries(settings.replyTypes).map(([type, enabled]) => (
            <label key={type} className="flex items-center justify-between">
              <div>
                <span className="text-sm text-gray-700 capitalize">{type}</span>
                <p className="text-xs text-gray-500">
                  {type === 'helpful' && 'Provide helpful information and tips'}
                  {type === 'engaging' && 'Ask questions and start conversations'}
                  {type === 'promotional' && 'Subtly promote your content'}
                </p>
              </div>
              <input
                type="checkbox"
                checked={enabled as boolean}
                onChange={(e) => onChange({
                  ...settings,
                  replyTypes: {
                    ...settings.replyTypes,
                    [type]: e.target.checked
                  }
                })}
                className="w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500"
              />
            </label>
          ))}
        </div>
      </div>
    </div>
  );
};

export default BotControl;