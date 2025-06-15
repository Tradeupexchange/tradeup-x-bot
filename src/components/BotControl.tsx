import React, { useState, useEffect } from 'react';
import { Play, Square, RefreshCw, AlertCircle, CheckCircle, MessageSquare, Reply, Settings, Clock, Target } from 'lucide-react';
import { useApi, apiCall } from '../hooks/useApi';

interface BotJob {
  id: string;
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

const BotControl: React.FC = () => {
  const { data: status, loading, refetch } = useApi('/api/bot-status');
  const [jobs, setJobs] = useState<BotJob[]>([]);
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [showScheduler, setShowScheduler] = useState(false);

  useEffect(() => {
    if (status?.jobs) {
      setJobs(status.jobs);
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

  const createNewJob = async (type: 'posting' | 'replying', settings: any) => {
    try {
      setActionLoading('create');
      console.log('Creating new job:', { type, settings });
      
      const result = await apiCall('/api/bot-job/create', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ type, settings })
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

  if (loading) {
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
            <div className={`p-3 rounded-full ${
              status?.running ? 'bg-green-100' : 'bg-gray-100'
            }`}>
              {status?.running ? (
                <CheckCircle className="h-6 w-6 text-green-600" />
              ) : (
                <AlertCircle className="h-6 w-6 text-gray-600" />
              )}
            </div>
            <div>
              <h3 className="text-xl font-semibold text-gray-900">
                Pokemon TCG Bot Control Center
              </h3>
              <p className="text-sm text-gray-600">
                Manage your automated posting and reply functions
              </p>
            </div>
          </div>
          
          <button
            onClick={() => setShowScheduler(true)}
            disabled={actionLoading === 'create'}
            className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors duration-200"
          >
            {actionLoading === 'create' ? (
              <RefreshCw className="h-4 w-4 animate-spin" />
            ) : (
              <Play className="h-4 w-4" />
            )}
            <span>{actionLoading === 'create' ? 'Creating...' : 'New Job'}</span>
          </button>
        </div>

        {/* Quick Stats */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-blue-50 rounded-lg p-4">
            <div className="flex items-center space-x-2">
              <MessageSquare className="h-5 w-5 text-blue-600" />
              <span className="text-sm font-medium text-blue-900">Posts Today</span>
            </div>
            <p className="text-2xl font-bold text-blue-900 mt-1">
              {status?.stats?.postsToday || 0}
            </p>
          </div>
          
          <div className="bg-green-50 rounded-lg p-4">
            <div className="flex items-center space-x-2">
              <Reply className="h-5 w-5 text-green-600" />
              <span className="text-sm font-medium text-green-900">Replies Today</span>
            </div>
            <p className="text-2xl font-bold text-green-900 mt-1">
              {status?.stats?.repliesToday || 0}
            </p>
          </div>
          
          <div className="bg-purple-50 rounded-lg p-4">
            <div className="flex items-center space-x-2">
              <Target className="h-5 w-5 text-purple-600" />
              <span className="text-sm font-medium text-purple-900">Success Rate</span>
            </div>
            <p className="text-2xl font-bold text-purple-900 mt-1">
              {status?.stats?.successRate || 0}%
            </p>
          </div>
        </div>
      </div>

      {/* Active Jobs */}
      <div className="bg-white rounded-xl p-6 shadow-sm">
        <h4 className="text-lg font-semibold text-gray-900 mb-4">Active Jobs</h4>
        
        {jobs.length === 0 ? (
          <div className="text-center py-8">
            <AlertCircle className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <p className="text-gray-500 mb-4">No active jobs running</p>
            <button
              onClick={() => setShowScheduler(true)}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors duration-200"
            >
              Create Your First Job
            </button>
          </div>
        ) : (
          <div className="space-y-4">
            {jobs.map((job) => (
              <JobCard
                key={job.id}
                job={job}
                onAction={handleJobAction}
                actionLoading={actionLoading}
              />
            ))}
          </div>
        )}
      </div>

      {/* Job Scheduler Modal */}
      {showScheduler && (
        <JobScheduler
          onClose={() => setShowScheduler(false)}
          onCreateJob={createNewJob}
          loading={actionLoading === 'create'}
        />
      )}
    </div>
  );
};

interface JobCardProps {
  job: BotJob;
  onAction: (jobId: string, action: 'start' | 'stop' | 'pause') => void;
  actionLoading: string | null;
}

const JobCard: React.FC<JobCardProps> = ({ job, onAction, actionLoading }) => {
  const isRunning = job.status === 'running';
  const isLoading = actionLoading?.startsWith(job.id);

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
          
          <div>
            <h5 className="font-medium text-gray-900 capitalize">
              {job.type} Bot
            </h5>
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

interface JobSchedulerProps {
  onClose: () => void;
  onCreateJob: (type: 'posting' | 'replying', settings: any) => void;
  loading: boolean;
}

const JobScheduler: React.FC<JobSchedulerProps> = ({ onClose, onCreateJob, loading }) => {
  const [jobType, setJobType] = useState<'posting' | 'replying'>('posting');
  const [settings, setSettings] = useState({
    // Posting settings
    postsPerDay: 12,
    postingHours: { start: 9, end: 21 },
    contentTypes: {
      cardPulls: true,
      deckBuilding: true,
      marketAnalysis: true,
      tournaments: true
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

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    console.log('Submitting job creation:', { type: jobType, settings });
    onCreateJob(jobType, settings);
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <div className="p-6 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <h3 className="text-xl font-semibold text-gray-900">Create New Bot Job</h3>
            <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
              <RefreshCw className="h-5 w-5" />
            </button>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-6">
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

          {/* Job-specific settings */}
          {jobType === 'posting' ? (
            <PostingSettings settings={settings} onChange={setSettings} />
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
              ) : (
                <Play className="h-4 w-4" />
              )}
              <span>{loading ? 'Creating...' : 'Start Job'}</span>
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
    </div>
  );
};

const PostingSettings: React.FC<{ settings: any; onChange: (settings: any) => void }> = ({
  settings,
  onChange
}) => {
  return (
    <div className="space-y-4">
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Posts per day: {settings.postsPerDay}
        </label>
        <input
          type="range"
          min="1"
          max="50"
          value={settings.postsPerDay}
          onChange={(e) => onChange({
            ...settings,
            postsPerDay: parseInt(e.target.value)
          })}
          className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
        />
        <div className="flex justify-between text-xs text-gray-500 mt-1">
          <span>1</span>
          <span>25</span>
          <span>50</span>
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Active Hours
        </label>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="text-xs text-gray-500">Start Time</label>
            <select
              value={settings.postingHours.start}
              onChange={(e) => onChange({
                ...settings,
                postingHours: {
                  ...settings.postingHours,
                  start: parseInt(e.target.value)
                }
              })}
              className="w-full mt-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            >
              {Array.from({ length: 24 }, (_, i) => (
                <option key={i} value={i}>
                  {i.toString().padStart(2, '0')}:00
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="text-xs text-gray-500">End Time</label>
            <select
              value={settings.postingHours.end}
              onChange={(e) => onChange({
                ...settings,
                postingHours: {
                  ...settings.postingHours,
                  end: parseInt(e.target.value)
                }
              })}
              className="w-full mt-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            >
              {Array.from({ length: 24 }, (_, i) => (
                <option key={i} value={i}>
                  {i.toString().padStart(2, '0')}:00
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-3">
          Content Types to Post
        </label>
        <div className="space-y-2">
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