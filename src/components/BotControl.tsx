import React, { useState, useEffect } from 'react';
import { Play, Square, RefreshCw, AlertCircle, CheckCircle, MessageSquare, Reply, Settings, Clock, Target, Eye, Check, X, Calendar, Plus, Trash2, Edit2, RotateCcw, ExternalLink } from 'lucide-react';
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
}

interface BotStatus {
  running: boolean;
  uptime: string | null;
  lastRun: string | null;
  jobs: BotJob[];
  timestamp: string;
}

interface GeneratedContent {
  id: string;
  content: string;
  type: 'post' | 'reply';
  topic?: string;
  originalTweet?: string;
  tweetId?: string;
  tweetAuthor?: string;
  approved: boolean | null; // null = pending, true = approved, false = rejected
  scheduledTime?: string;
  engagement_score?: number;
  hashtags?: string[];
  mentions_tradeup?: boolean;
  tweetIndex?: number; // Track which tweet from the sheet this is
  autoPost?: boolean; // Flag for immediate posting after approval
  originalTweetUrl?: string; // Direct link to original tweet
}

interface JobSettings {
  postsPerDay?: number;
  topics?: string[];
  postingTimeStart?: string;
  postingTimeEnd?: string;
  postingDate?: string;
  contentTypes?: {
    cardPulls: boolean;
    deckBuilding: boolean;
    marketAnalysis: boolean;
    tournaments: boolean;
  };
  // Reply settings (simplified)
  maxRepliesPerHour?: number;
}

interface PostedReply {
  id: string;
  content: string;
  originalTweet: string;
  tweetAuthor: string;
  replyUrl: string;
  originalTweetUrl: string;
  postedAt: string;
}

interface BotControlProps {
  onPostSuccess?: () => void;
  onJobCreated?: () => void;
}

const BotControl: React.FC<BotControlProps> = ({ onPostSuccess, onJobCreated }) => {
  // Use the centralized useApi hook
  const { data: status, loading, error, lastFetch, refetch } = useApi<BotStatus>('/api/bot-status');
  
  const [jobs, setJobs] = useState<BotJob[]>([]);
  const [jobCounter, setJobCounter] = useState(1);
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [showScheduler, setShowScheduler] = useState(false);
  const [showContentApproval, setShowContentApproval] = useState(false);
  const [generatedContent, setGeneratedContent] = useState<GeneratedContent[]>([]);
  const [currentJobSettings, setCurrentJobSettings] = useState<JobSettings | null>(null);
  const [editingJobId, setEditingJobId] = useState<string | null>(null);
  const [editingJobName, setEditingJobName] = useState('');
  const [apiError, setApiError] = useState<string | null>(null);
  const [currentJobType, setCurrentJobType] = useState<'posting' | 'replying'>('posting');
  const [postedReplies, setPostedReplies] = useState<PostedReply[]>([]);
  const [showPostedReplies, setShowPostedReplies] = useState(false);

  // Update jobs when status changes (filter out demo jobs)
  useEffect(() => {
    if (status?.jobs && Array.isArray(status.jobs)) {
      // Filter out demo jobs
      const realJobs = status.jobs.filter(job => !job.id.includes('demo'));
      setJobs(realJobs);
      
      // Update job counter based on existing jobs
      const maxJobNumber = realJobs.reduce((max, job) => {
        const jobNamePattern = /^Job #(\d+)$/;
        const match = job.name?.match(jobNamePattern);
        if (match) {
          return Math.max(max, parseInt(match[1], 10));
        }
        return max;
      }, 0);
      setJobCounter(maxJobNumber + 1);
      console.log('Updated jobs from API:', realJobs);
    }
  }, [status]);

  const handleJobAction = async (jobId: string, action: 'start' | 'stop' | 'pause') => {
    try {
      setActionLoading(`${jobId}-${action}`);
      setApiError(null);
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
      setApiError(`Failed to ${action} job: ${error instanceof Error ? error.message : 'Unknown error'}`);
      setActionLoading(null);
    }
  };

  const handleJobRename = async (jobId: string, newName: string) => {
    try {
      setApiError(null);
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
      setApiError(`Failed to rename job: ${error instanceof Error ? error.message : 'Unknown error'}`);
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

  const createJobWithApproval = async (jobSettings: JobSettings, jobName: string, jobType: 'posting' | 'replying') => {
    try {
      setActionLoading('generate-content');
      setApiError(null);
      console.log(`🧪 Creating ${jobType} job with approval workflow...`);

      // Use provided name or generate automatic name
      const finalJobName = jobName.trim() || `Job #${jobCounter}`;
      if (!jobName.trim()) {
        setJobCounter(prev => prev + 1);
      }

      let content: GeneratedContent[] = [];

      if (jobType === 'posting') {
        // Generate posts for approval
        console.log('📝 Generating posts for approval...');
        
        for (let i = 0; i < (jobSettings.postsPerDay || 5); i++) {
          const randomTopic = jobSettings.topics?.[Math.floor(Math.random() * jobSettings.topics.length)] || 'Pokemon TCG';
          
          const contentResult = await apiCall('/api/generate-content', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              topic: randomTopic,
              count: 1
            })
          });

          if (contentResult.success && contentResult.content) {
            content.push({
              id: `post-${Date.now()}-${i}`,
              content: contentResult.content.content || contentResult.content,
              type: 'post',
              topic: randomTopic,
              approved: null,
              engagement_score: contentResult.content.engagement_score,
              hashtags: contentResult.content.hashtags,
              mentions_tradeup: contentResult.content.mentions_tradeup
            });
          }
        }

        // Generate scheduled times for posts
        const scheduledTimes = generateScheduledTimes(
          jobSettings.postsPerDay || 5,
          jobSettings.postingTimeStart || '09:00',
          jobSettings.postingTimeEnd || '17:00'
        );

        // Assign scheduled times to posts
        content.forEach((item, index) => {
          item.scheduledTime = scheduledTimes[index];
        });

      } else if (jobType === 'replying') {
        // Generate ALL replies at once instead of one by one
        console.log('📝 Generating all replies for approval...');
        
        const numReplies = jobSettings.maxRepliesPerHour || 5;
        
        // Fetch tweets from Google Sheets
        const tweetsResult = await apiCall('/api/fetch-tweets-from-sheets', {
          method: 'GET'
        });

        if (!tweetsResult.success || !tweetsResult.tweets || tweetsResult.tweets.length === 0) {
          setApiError('No tweets found in Google Sheets to reply to. Please check your Google Sheets setup.');
          setActionLoading(null);
          return;
        }
      

        // Generate replies for the requested number of tweets
        const tweetsToProcess = tweetsResult.tweets.slice(0, numReplies);
        
        for (let i = 0; i < tweetsToProcess.length; i++) {
          const tweet = tweetsToProcess[i];
          
          try {
            const replyResult = await apiCall('/api/generate-reply', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({
                tweet_text: tweet.text,
                tweet_author: tweet.author
              })
            });

            if (replyResult.success && replyResult.reply) {
              content.push({
                id: `reply-${Date.now()}-${i}`,
                content: replyResult.reply,
                type: 'reply',
                originalTweet: tweet.text,
                tweetId: tweet.id,
                tweetAuthor: tweet.author,
                approved: null,
                scheduledTime: 'On Approval',
                tweetIndex: i,
                autoPost: true,
                originalTweetUrl: `https://twitter.com/${tweet.author}/status/${tweet.id}`
              });
            }
          } catch (error) {
            console.error(`Error generating reply for tweet ${i}:`, error);
          }
        }

        if (content.length === 0) {
          setApiError('Failed to generate any replies. Please try again.');
          setActionLoading(null);
          return;
        }
      }

      setGeneratedContent(content);
      setCurrentJobSettings({ ...jobSettings, name: finalJobName } as any);
      setCurrentJobType(jobType);
      setShowScheduler(false);
      setShowContentApproval(true);

    } catch (error) {
      console.error('❌ Content generation failed:', error);
      setApiError(`Failed to generate content: ${error instanceof Error ? error.message : 'Unknown error'}`);
    } finally {
      setActionLoading(null);
    }
    const handleCloseContentApproval = () => {
      setShowContentApproval(false);
      setGeneratedContent([]);
      setCurrentJobSettings(null);
  };

  const approveContent = (contentId: string) => {
    setGeneratedContent(prev => 
      prev.map(item => 
        item.id === contentId ? { ...item, approved: true } : item
      )
    );
  };

  const regenerateContent = async (contentId: string) => {
    try {
      setActionLoading(`regenerate-${contentId}`);
      setApiError(null);
      const contentItem = generatedContent.find(c => c.id === contentId);
      if (!contentItem) return;

      if (contentItem.type === 'post') {
        const contentResult = await apiCall('/api/generate-content', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            topic: contentItem.topic,
            count: 1
          })
        });

        if (contentResult.success && contentResult.content) {
          setGeneratedContent(prev => 
            prev.map(c => 
              c.id === contentId 
                ? {
                    ...c,
                    content: contentResult.content.content || contentResult.content,
                    approved: null,
                    engagement_score: contentResult.content.engagement_score,
                    hashtags: contentResult.content.hashtags,
                    mentions_tradeup: contentResult.content.mentions_tradeup
                  }
                : c
            )
          );
        }
      } else if (contentItem.type === 'reply') {
        // For replies, regenerate a new reply to the same tweet
        const replyResult = await apiCall('/api/generate-reply', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            tweet_text: contentItem.originalTweet,
            tweet_author: contentItem.tweetAuthor
          })
        });

        if (replyResult.success && replyResult.reply) {
          setGeneratedContent(prev => 
            prev.map(c => 
              c.id === contentId 
                ? {
                    ...c,
                    content: replyResult.reply,
                    approved: null
                  }
                : c
            )
          );
        }
      }
    } catch (error) {
      console.error('❌ Content regeneration failed:', error);
      setApiError(`Failed to regenerate content: ${error instanceof Error ? error.message : 'Unknown error'}`);
    } finally {
      setActionLoading(null);
    }
  };

  const regenerateForDifferentTweet = async (contentId: string) => {
    try {
      setActionLoading(`regenerate-different-${contentId}`);
      setApiError(null);
      const contentItem = generatedContent.find(c => c.id === contentId);
      if (!contentItem) return;

      if (contentItem.type === 'reply') {
        // For replies, get a different tweet from the sheets and generate a reply to that
        const tweetsResult = await apiCall('/api/fetch-tweets-from-sheets', {
          method: 'GET'
        });

        if (tweetsResult.success && tweetsResult.tweets && tweetsResult.tweets.length > 0) {
          // Filter out the current tweet and pick a random different one
          const differentTweets = tweetsResult.tweets.filter((tweet: any) => tweet.id !== contentItem.tweetId);
          
          if (differentTweets.length === 0) {
            setApiError('No other tweets available to generate a different reply.');
            setActionLoading(null);
            return;
          }

          const randomTweet = differentTweets[Math.floor(Math.random() * differentTweets.length)];

          const replyResult = await apiCall('/api/generate-reply', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              tweet_text: randomTweet.text,
              tweet_author: randomTweet.author
            })
          });

          if (replyResult.success && replyResult.reply) {
            setGeneratedContent(prev => 
              prev.map(c => 
                c.id === contentId 
                  ? {
                      ...c,
                      content: replyResult.reply,
                      originalTweet: randomTweet.text,
                      tweetId: randomTweet.id,
                      tweetAuthor: randomTweet.author,
                      originalTweetUrl: `https://twitter.com/${randomTweet.author}/status/${randomTweet.id}`,
                      approved: null
                    }
                  : c
              )
            );
          }
        }
      } else if (contentItem.type === 'post') {
        // For posts, generate with a different topic
        const availableTopics = (currentJobSettings as any)?.topics || ['Pokemon TCG', 'Card Pulls', 'Deck Building', 'Tournaments'];
        const differentTopics = availableTopics.filter((topic: string) => topic !== contentItem.topic);
        
        if (differentTopics.length === 0) {
          // If no different topics, just regenerate with the same topic
          await regenerateContent(contentId);
          return;
        }

        const randomTopic = differentTopics[Math.floor(Math.random() * differentTopics.length)];

        const contentResult = await apiCall('/api/generate-content', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            topic: randomTopic,
            count: 1
          })
        });

        if (contentResult.success && contentResult.content) {
          setGeneratedContent(prev => 
            prev.map(c => 
              c.id === contentId 
                ? {
                    ...c,
                    content: contentResult.content.content || contentResult.content,
                    topic: randomTopic,
                    approved: null,
                    engagement_score: contentResult.content.engagement_score,
                    hashtags: contentResult.content.hashtags,
                    mentions_tradeup: contentResult.content.mentions_tradeup
                  }
                : c
            )
          );
        }
      }
    } catch (error) {
      console.error('❌ Content regeneration for different item failed:', error);
      setApiError(`Failed to regenerate content: ${error instanceof Error ? error.message : 'Unknown error'}`);
    } finally {
      setActionLoading(null);
    }
  };

  const scheduleApprovedContent = async () => {
    try {
      setActionLoading('schedule');
      setApiError(null);
      const approvedItems = generatedContent.filter(item => item.approved === true);
      
      if (approvedItems.length === 0) {
        setApiError('Please approve at least one item before posting.');
        return;
      }

      console.log(`📅 Processing approved ${currentJobType}...`, approvedItems);

      if (currentJobType === 'replying') {
        // For replies, post them immediately and collect results
        console.log('🚀 Posting replies immediately...');
        
        let successCount = 0;
        const postedRepliesData: PostedReply[] = [];

        for (const reply of approvedItems) {
          try {
            console.log(`📤 Posting reply to tweet ${reply.tweetId}...`);
            
            const postResult = await apiCall('/api/post-reply-with-tracking', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({
                content: reply.content,
                reply_to_tweet_id: reply.tweetId,
                original_tweet_author: reply.tweetAuthor,
                original_tweet_content: reply.originalTweet
              })
            });

            console.log('🔍 FULL POST RESULT:', postResult);
            console.log('🔍 POST RESULT SUCCESS:', postResult.success);
            console.log('🔍 POST RESULT TYPE:', typeof postResult.success);

            if (postResult.success) {
              successCount++;
              console.log('✅ Success! Count is now:', successCount);
              
              // Collect posted reply data for UI display
              postedRepliesData.push({
                id: postResult.tweet_id || `reply_${Date.now()}_${successCount}`,
                content: reply.content,
                originalTweet: reply.originalTweet || '',
                tweetAuthor: reply.tweetAuthor || '',
                replyUrl: postResult.tweet_url || `https://twitter.com/TradeUpApp/status/${postResult.tweet_id}`,
                originalTweetUrl: reply.originalTweetUrl || `https://twitter.com/${reply.tweetAuthor}/status/${reply.tweetId}`,
                postedAt: new Date().toISOString()
              });
              
              console.log(`✅ Successfully posted reply to @${reply.tweetAuthor}`);
            } else {
              console.log('❌ postResult.success was false/undefined');
              console.log('🔍 Actual value:', postResult.success);
              console.error(`❌ Failed to post reply to @${reply.tweetAuthor}:`, postResult.error);
            }
          } catch (error) {
            console.error(`❌ Error posting reply to @${reply.tweetAuthor}:`, error);
          }
        }

        // Update UI to show posted replies instead of popup
        if (successCount > 0) {
          setPostedReplies(postedRepliesData);
          setShowPostedReplies(true);
          
          // Call the refresh callback after successful posts
          if (onPostSuccess) {
            console.log('🔄 BotControl: Triggering post refresh after replies...');
            setTimeout(() => {
              onPostSuccess();
            }, 2000);
          }
        } else {
          setApiError('No replies were successfully posted. Please check your Twitter API connection.');
        }

        setShowContentApproval(false);
        setGeneratedContent([]);

      } else {
        // For posts, use the original scheduling logic
        const endpoint = '/api/bot-job/create-posting-job';

        const result = await apiCall(endpoint, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            type: currentJobType,
            name: (currentJobSettings as any)?.name || 'Untitled Job',
            settings: {
              ...currentJobSettings,
              approvedContent: approvedItems,
              autoPost: true
            }
          })
        });

        if (result.success) {
          alert(`Successfully scheduled ${approvedItems.length} posts!`);
          setShowContentApproval(false);
          setGeneratedContent([]);
          refetch(); // Refresh the jobs list
        }
      }

    } catch (error) {
      console.error('❌ Processing failed:', error);
      setApiError(`Failed to process content: ${error instanceof Error ? error.message : 'Unknown error'}`);
    } finally {
      setActionLoading(null);
    }
  };

  const createNewJob = async (type: 'posting' | 'replying', settings: any, jobName: string) => {
    try {
      setActionLoading('create');
      setApiError(null);
      
      // Use provided name or generate automatic name
      const finalJobName = jobName.trim() || `Job #${jobCounter}`;
      if (!jobName.trim()) {
        setJobCounter(prev => prev + 1);
      }
      
      console.log('Creating new job:', { type, settings, name: finalJobName });
      
      // Use the correct endpoint based on job type
      const endpoint = type === 'posting' 
        ? '/api/bot-job/create-posting-job'
        : '/api/bot-job/create-reply-job';
      
      const result = await apiCall(endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
          type, 
          settings, 
          name: finalJobName,
          // Add specific fields for reply jobs
          ...(type === 'replying' && {
            maxRepliesPerHour: settings.maxRepliesPerHour,
            autoReply: false,
            sentiment_filter: 'positive'
          })
        })
      });
      
      console.log('Job creation result:', result);
      
      if (result.success) {
        // Refetch status to get updated jobs list
        refetch();
        setShowScheduler(false);
        alert(`${type} job created successfully!`);
        
        // Call the job created callback
        if (onJobCreated) {
          onJobCreated();
        }
      } else {
        throw new Error(result.error || 'Job creation failed');
      }
      
    } catch (error) {
      console.error('Error creating job:', error);
      setApiError(`Failed to create job: ${error instanceof Error ? error.message : 'Unknown error'}`);
    } finally {
      setActionLoading(null);
    }
  };

  // Posted Replies Modal Component
  const PostedRepliesModal: React.FC<{
    replies: PostedReply[];
    onClose: () => void;
  }> = ({ replies, onClose }) => {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
        <div className="bg-white rounded-xl max-w-4xl w-full max-h-[80vh] overflow-y-auto shadow-2xl">
          <div className="p-6 border-b border-gray-200">
            <div className="flex items-center justify-between">
              <h3 className="text-xl font-semibold text-gray-900">
                Successfully Posted {replies.length} Replies
              </h3>
              <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
                <X className="h-5 w-5" />
              </button>
            </div>
            <p className="text-sm text-gray-600 mt-2">
              Your replies have been posted to Twitter. Click the links below to view them.
            </p>
          </div>

          <div className="p-6 space-y-6">
            {replies.map((reply, index) => (
              <div key={reply.id} className="border-l-4 border-green-500 bg-green-50 rounded-lg p-4">
                <div className="flex items-start justify-between mb-3">
                  <div className="flex items-center space-x-2">
                    <span className="bg-green-100 text-green-800 px-2 py-1 text-xs font-medium rounded-full">
                      Reply #{index + 1}
                    </span>
                    <span className="text-xs text-gray-500">
                      {new Date(reply.postedAt).toLocaleTimeString()}
                    </span>
                  </div>
                  <div className="flex space-x-2">
                    <a
                      href={reply.originalTweetUrl}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-xs text-blue-600 hover:text-blue-800 underline flex items-center space-x-1"
                    >
                      <ExternalLink className="h-3 w-3" />
                      <span>Original Tweet</span>
                    </a>
                    <a
                      href={reply.replyUrl}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-xs text-green-600 hover:text-green-800 underline flex items-center space-x-1 font-medium"
                    >
                      <ExternalLink className="h-3 w-3" />
                      <span>View Reply</span>
                    </a>
                  </div>
                </div>

                {/* Original Tweet Context */}
                <div className="mb-3 p-3 bg-gray-100 rounded-lg">
                  <p className="text-sm text-gray-600 mb-1">
                    Original tweet from @{reply.tweetAuthor}:
                  </p>
                  <p className="text-sm text-gray-800 italic">
                    "{reply.originalTweet}"
                  </p>
                </div>

                {/* Your Reply */}
                <div className="mb-3">
                  <p className="text-sm text-gray-600 mb-1 font-medium">Your reply:</p>
                  <p className="text-gray-900 leading-relaxed font-medium">
                    {reply.content}
                  </p>
                </div>

                {/* Status */}
                <div className="flex items-center space-x-2">
                  <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
                  <span className="text-xs text-green-800 font-medium">
                    Successfully posted to Twitter
                  </span>
                </div>
              </div>
            ))}
          </div>

          <div className="p-6 border-t border-gray-200 bg-gray-50">
            <div className="flex justify-between items-center">
              <div className="text-sm text-gray-600">
                All replies have been posted and will appear in your Recent Posts section.
              </div>
              <button
                onClick={onClose}
                className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors duration-200"
              >
                Done
              </button>
            </div>
          </div>
        </div>
      </div>
    );
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
                Automated Engagement
              </h3>
              <p className="text-sm text-gray-600">
                Generate, approve, and schedule posts and replies
              </p>
            </div>
          </div>
          
          <div className="flex space-x-3">
            <button
              onClick={() => setShowScheduler(true)}
              disabled={actionLoading === 'create'}
              className="flex items-center justify-center space-x-2 px-8 py-3 bg-blue-600 text-white text-base font-medium rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors duration-200 min-w-[200px]"
            >
              {actionLoading === 'create' ? (
                <RefreshCw className="h-5 w-5 animate-spin" />
              ) : (
                <Calendar className="h-5 w-5" />
              )}
              <span>{actionLoading === 'create' ? 'Creating...' : 'New Job'}</span>
            </button>

            {loading && (
              <div className="flex items-center space-x-2 px-4 py-2 bg-gray-100 text-gray-600 rounded-lg">
                <RefreshCw className="h-4 w-4 animate-spin" />
                <span>Updating...</span>
              </div>
            )}
          </div>
        </div>

        {/* Error display */}
        {(error || apiError) && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-sm text-red-700">⚠️ {error || apiError}</p>
            <button 
              onClick={() => {setApiError(null); refetch();}}
              className="text-sm text-red-600 hover:text-red-800 underline mt-1"
            >
              Clear error and retry
            </button>
          </div>
        )}
      </div>

      {/* Active Jobs */}
      <div className="bg-white rounded-xl p-6 shadow-sm">
        <h4 className="text-lg font-semibold text-gray-900 mb-4">Scheduled Posting Jobs</h4>
        
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
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <EnhancedJobScheduler
            onClose={() => setShowScheduler(false)}
            onCreateJob={createNewJob}
            onCreateJobWithApproval={createJobWithApproval}
            loading={actionLoading === 'create' || actionLoading === 'generate-content'}
          />
        </div>
      )}

      {/* Content Approval Modal */}
      {showContentApproval && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <ContentApprovalModal
            content={generatedContent}
            contentType={currentJobType}
            onApprove={approveContent}
            onRegenerate={regenerateContent}
            onRegenerateForDifferent={regenerateForDifferentTweet}
            onSchedule={scheduleApprovedContent}
            onClose={handleCloseContentApproval}
            loading={actionLoading}
          />
        </div>
      )}

      {/* Posted Replies Display Modal */}
      {showPostedReplies && (
        <PostedRepliesModal
          replies={postedReplies}
          onClose={() => {
            setShowPostedReplies(false);
            setPostedReplies([]);
          }}
        />
      )}
    </div>
  );
};

// Enhanced Job Scheduler with unified workflow
interface EnhancedJobSchedulerProps {
  onClose: () => void;
  onCreateJob: (type: 'posting' | 'replying', settings: any, jobName: string) => void;
  onCreateJobWithApproval: (settings: JobSettings, jobName: string, jobType: 'posting' | 'replying') => void;
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
    postingDate: new Date().toISOString().split('T')[0],
    contentTypes: {
      cardPulls: true,
      deckBuilding: true,
      marketAnalysis: true,
      tournaments: false
    },
    
    // Reply settings (simplified)
    maxRepliesPerHour: 10
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
      if (useApprovalWorkflow) {
        // Use the enhanced workflow with content approval for both posting and replying
        const jobSettings: JobSettings = jobType === 'posting' ? {
          postsPerDay: settings.postsPerDay,
          topics: settings.topics,
          postingTimeStart: settings.postingTimeStart,
          postingTimeEnd: settings.postingTimeEnd,
          postingDate: settings.postingDate,
          contentTypes: settings.contentTypes
        } : {
          maxRepliesPerHour: settings.maxRepliesPerHour
        };
        onCreateJobWithApproval(jobSettings, jobName, jobType);
      } else {
        // Use the original workflow
        onCreateJob(jobType, settings, jobName);
      }
    } catch (error) {
      console.error('Error in form submission:', error);
    }
  };

  return (
    <div className="bg-white rounded-xl max-w-3xl w-full max-h-[90vh] overflow-y-auto shadow-2xl">
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
        {jobType === 'posting' && (
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Job Name (optional)
            </label>
            <input
              type="text"
              value={jobName}
              onChange={(e) => setJobName(e.target.value)}
              placeholder="Enter a name for this job or leave empty for auto-generation"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
        )}

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

        {/* Approval Workflow Toggle */}
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
                Use Content Approval Workflow
              </span>
              <p className="text-xs text-blue-700">
                Generate content for review before scheduling (Recommended)
              </p>
            </div>
          </label>
        </div>

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
            ) : useApprovalWorkflow ? (
              <Eye className="h-4 w-4" />
            ) : (
              <Play className="h-4 w-4" />
            )}
            <span>
              {loading ? 'Processing...' : 
               useApprovalWorkflow ? 'Generate for Approval' : 'Start Job'
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

      {/* Posting date and time range */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Posting Schedule
        </label>
        <div className="grid grid-cols-3 gap-4">
          <div>
            <label className="text-xs text-gray-500">Date</label>
            <input
              type="date"
              value={settings.postingDate}
              min={new Date().toISOString().split('T')[0]}
              onChange={(e) => onChange({
                ...settings,
                postingDate: e.target.value
              })}
              className="w-full mt-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            />
          </div>
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

// Simplified Replying Settings Component - Just number of replies
const ReplyingSettings: React.FC<{ settings: any; onChange: (settings: any) => void }> = ({
  settings,
  onChange
}) => {
  return (
    <div className="space-y-6">
      {/* Number of replies to generate and post */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Number of Replies to Generate: {settings.maxRepliesPerHour}
        </label>
        <input
          type="range"
          min="1"
          max="20"
          value={settings.maxRepliesPerHour}
          onChange={(e) => onChange({
            ...settings,
            maxRepliesPerHour: parseInt(e.target.value)
          })}
          className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
        />
        <div className="flex justify-between text-xs text-gray-500 mt-1">
          <span>1</span>
          <span>10</span>
          <span>20</span>
        </div>
      </div>

      {/* Auto-posting notice */}
      <div className="bg-green-50 border border-green-200 rounded-lg p-4">
        <div className="flex items-start space-x-2">
          <CheckCircle className="h-5 w-5 text-green-600 flex-shrink-0 mt-0.5" />
          <div>
            <h4 className="text-sm font-medium text-green-900">Instant Reply Workflow</h4>
            <p className="text-xs text-green-700 mt-1">
              Replies will be generated from your Google Sheet, shown for approval, then automatically posted to Twitter once approved. 
              They'll appear in your Recent Posts section with direct links to the original tweets.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

// Updated Content Approval Modal with enhanced action buttons and tooltips
interface ContentApprovalModalProps {
  content: GeneratedContent[];
  contentType: 'posting' | 'replying';
  onApprove: (contentId: string) => void;
  onRegenerate: (contentId: string) => void;
  onRegenerateForDifferent: (contentId: string) => void;
  onSchedule: () => void;
  onClose: () => void;
  loading: string | null;
}

const ContentApprovalModal: React.FC<ContentApprovalModalProps> = ({
  content,
  contentType,
  onApprove,
  onRegenerate,
  onRegenerateForDifferent,
  onSchedule,
  onClose,
  loading
}) => {
  const approvedCount = content.filter(c => c.approved === true).length;
  const rejectedCount = content.filter(c => c.approved === false).length;
  const pendingCount = content.filter(c => c.approved === null).length;

  const contentTypeLabel = contentType === 'posting' ? 'Posts' : 'Replies';
  const actionLabel = contentType === 'posting' ? 'Schedule' : 'Post Now';

  return (
    <div className="bg-white rounded-xl max-w-5xl w-full max-h-[90vh] overflow-y-auto shadow-2xl">
      <div className="p-6 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <h3 className="text-xl font-semibold text-gray-900">Review & Approve {contentTypeLabel}</h3>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
            <X className="h-5 w-5" />
          </button>
        </div>
        
        {/* Updated notice for replies */}
        {contentType === 'replying' && (
          <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
            <p className="text-sm text-blue-800">
              🚀 <strong>Instant Posting:</strong> Approved replies will be posted immediately to Twitter and appear in your Recent Posts section with links to the original tweets.
            </p>
          </div>
        )}
        
        {/* Stats bar */}
        <div className="mt-4 grid grid-cols-4 gap-4 text-sm">
          <div className="bg-blue-50 rounded-lg p-3 text-center">
            <div className="font-semibold text-blue-900">{content.length}</div>
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

      {/* Content list */}
      <div className="p-6 space-y-4 max-h-96 overflow-y-auto">
        {content.map((item) => (
          <div
            key={item.id}
            className={`p-4 border-2 rounded-lg transition-all duration-200 ${
              item.approved === true
                ? 'border-green-200 bg-green-50'
                : item.approved === false
                ? 'border-red-200 bg-red-50'
                : 'border-gray-200 bg-white hover:border-gray-300'
            }`}
          >
            <div className="flex items-start justify-between">
              <div className="flex-1 mr-4">
                {/* Content metadata */}
                <div className="flex items-center gap-2 mb-2">
                  {item.type === 'post' ? (
                    <>
                      <span className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded-full">
                        {item.topic}
                      </span>
                      <span className="text-xs text-gray-500 flex items-center gap-1">
                        <Clock className="h-3 w-3" />
                        {item.scheduledTime}
                      </span>
                      {item.mentions_tradeup && (
                        <span className="text-xs bg-purple-100 text-purple-800 px-2 py-1 rounded-full">
                          TradeUp Mention
                        </span>
                      )}
                    </>
                  ) : (
                    <>
                      <span className="text-xs bg-green-100 text-green-800 px-2 py-1 rounded-full">
                        Reply to @{item.tweetAuthor}
                      </span>
                      <span className="text-xs text-gray-500 flex items-center gap-1">
                        <Target className="h-3 w-3" />
                        {item.scheduledTime}
                      </span>
                      <a 
                        href={item.originalTweetUrl || `https://twitter.com/${item.tweetAuthor}/status/${item.tweetId}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-xs text-blue-600 hover:text-blue-800 underline flex items-center gap-1"
                      >
                        <ExternalLink className="h-3 w-3" />
                        View Original Tweet
                      </a>
                    </>
                  )}
                </div>

                {/* Original tweet for replies */}
                {item.type === 'reply' && item.originalTweet && (
                  <div className="mb-3 p-3 bg-gray-50 rounded-lg">
                    <p className="text-sm text-gray-600 mb-1">Original tweet:</p>
                    <p className="text-sm text-gray-800">{item.originalTweet}</p>
                  </div>
                )}

                {/* Content */}
                <p className="text-gray-900 mb-3 leading-relaxed">{item.content}</p>

                {/* Hashtags for posts */}
                {item.type === 'post' && item.hashtags && item.hashtags.length > 0 && (
                  <div className="flex gap-1 flex-wrap">
                    {item.hashtags.map((tag, i) => (
                      <span key={i} className="text-xs text-blue-600 bg-blue-50 px-2 py-1 rounded">
                        {tag}
                      </span>
                    ))}
                  </div>
                )}
              </div>
              
              {/* Enhanced Action buttons with tooltips */}
              <div className="flex gap-2 flex-shrink-0">
                {/* Approve Button - Green Check */}
                <div className="relative group">
                  <button
                    onClick={() => onApprove(item.id)}
                    disabled={item.approved === true}
                    className={`p-2 rounded-lg transition-all duration-200 ${
                      item.approved === true
                        ? 'bg-green-600 text-white cursor-default'
                        : 'bg-green-100 text-green-800 hover:bg-green-200 hover:scale-105'
                    }`}
                  >
                    <Check className="h-4 w-4" />
                  </button>
                  <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-2 py-1 bg-gray-900 text-white text-xs rounded opacity-0 group-hover:opacity-100 transition-opacity duration-200 whitespace-nowrap">
                    Approve
                  </div>
                </div>
                
                {/* Regenerate Same Content Button - Blue Circular Arrows */}
                <div className="relative group">
                  <button
                    onClick={() => onRegenerate(item.id)}
                    disabled={loading === `regenerate-${item.id}`}
                    className="p-2 rounded-lg bg-blue-100 text-blue-800 hover:bg-blue-200 hover:scale-105 transition-all duration-200 disabled:opacity-50"
                  >
                    {loading === `regenerate-${item.id}` ? (
                      <RefreshCw className="h-4 w-4 animate-spin" />
                    ) : (
                      <RotateCcw className="h-4 w-4" />
                    )}
                  </button>
                  <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-2 py-1 bg-gray-900 text-white text-xs rounded opacity-0 group-hover:opacity-100 transition-opacity duration-200 whitespace-nowrap">
                    {item.type === 'reply' ? 'Regenerate for this tweet' : 'Regenerate this content'}
                  </div>
                </div>

                {/* Regenerate Different Content Button - Red X */}
                <div className="relative group">
                  <button
                    onClick={() => onRegenerateForDifferent(item.id)}
                    disabled={loading === `regenerate-different-${item.id}`}
                    className="p-2 rounded-lg bg-red-100 text-red-800 hover:bg-red-200 hover:scale-105 transition-all duration-200 disabled:opacity-50"
                  >
                    {loading === `regenerate-different-${item.id}` ? (
                      <RefreshCw className="h-4 w-4 animate-spin" />
                    ) : (
                      <X className="h-4 w-4" />
                    )}
                  </button>
                  <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-2 py-1 bg-gray-900 text-white text-xs rounded opacity-0 group-hover:opacity-100 transition-opacity duration-200 whitespace-nowrap">
                    {item.type === 'reply' ? 'Regenerate for different tweet' : 'Regenerate different topic'}
                  </div>
                </div>
              </div>
            </div>

            {/* Approval status indicator */}
            {item.approved !== null && (
              <div className={`mt-3 pt-3 border-t ${
                item.approved ? 'border-green-200' : 'border-red-200'
              }`}>
                <span className={`text-xs font-medium ${
                  item.approved ? 'text-green-800' : 'text-red-800'
                }`}>
                  {item.approved 
                    ? contentType === 'posting' 
                      ? '✓ Approved for scheduling' 
                      : '✓ Approved for immediate posting'
                    : loading?.includes(item.id)
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
            ) : contentType === 'posting' ? (
              <Calendar className="h-4 w-4" />
            ) : (
              <Target className="h-4 w-4" />
            )}
            <span>
              {loading === 'schedule' ? 
                (contentType === 'posting' ? 'Scheduling...' : 'Posting...') : 
                `${actionLabel} ${approvedCount} Approved ${contentTypeLabel}`
              }
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
            Please approve at least one {contentType === 'posting' ? 'post' : 'reply'} before {contentType === 'posting' ? 'scheduling' : 'posting'}
          </p>
        )}
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
                : `${job.settings?.maxRepliesPerHour || 10} replies max`
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
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <span className="text-gray-500">Last Run:</span>
            <p className="font-medium">
              {job.lastRun ? new Date(job.lastRun).toLocaleString() : 'Never'}
            </p>
          </div>
          <div>
            <span className="text-gray-500">Next Scheduled Run:</span>
            <p className="font-medium">
              {job.nextRun ? new Date(job.nextRun).toLocaleString() : 'Not scheduled'}
            </p>
          </div>
        </div>
      </div>
    </div> 
  );
};

export default BotControl;