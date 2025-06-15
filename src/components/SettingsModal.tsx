import React, { useState, useEffect } from 'react';
import { X, Save, Bot, Clock, Hash, Target } from 'lucide-react';
import { useApi, apiCall } from '../hooks/useApi';

interface SettingsModalProps {
  onClose: () => void;
}

const SettingsModal: React.FC<SettingsModalProps> = ({ onClose }) => {
  const { data: currentSettings, loading } = useApi('/api/settings');
  const [settings, setSettings] = useState({
    postsPerDay: 12,
    keywords: ['Pokemon', 'TCG', 'Charizard', 'Pikachu', 'Tournament'],
    engagementMode: 'balanced',
    autoReply: true,
    contentTypes: {
      cardPulls: true,
      deckBuilding: true,
      marketAnalysis: true,
      tournaments: true
    }
  });
  const [saving, setSaving] = useState(false);
  const [saveMessage, setSaveMessage] = useState<string | null>(null);

  useEffect(() => {
    if (currentSettings) {
      console.log('Loaded settings:', currentSettings);
      setSettings(currentSettings);
    }
  }, [currentSettings]);

  const handleSave = async () => {
    try {
      setSaving(true);
      setSaveMessage(null);
      
      console.log('Saving settings:', settings);
      
      const result = await apiCall('/api/settings', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(settings)
      });
      
      console.log('Settings save result:', result);
      setSaveMessage('Settings saved successfully!');
      
      // Close modal after a brief delay
      setTimeout(() => {
        onClose();
      }, 1500);
    } catch (error) {
      console.error('Error saving settings:', error);
      setSaveMessage(`Error saving settings: ${error instanceof Error ? error.message : 'Unknown error'}`);
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
        <div className="bg-white rounded-xl max-w-2xl w-full p-8">
          <div className="animate-pulse space-y-4">
            <div className="h-8 bg-gray-200 rounded w-1/3"></div>
            <div className="space-y-3">
              <div className="h-4 bg-gray-200 rounded"></div>
              <div className="h-4 bg-gray-200 rounded w-5/6"></div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <div className="p-6 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <h2 className="text-2xl font-bold text-gray-900">Bot Settings</h2>
            <button 
              onClick={onClose}
              className="p-2 hover:bg-gray-100 rounded-lg transition-colors duration-150"
            >
              <X className="h-5 w-5" />
            </button>
          </div>
        </div>
        
        <div className="p-6 space-y-8">
          {/* Save Message */}
          {saveMessage && (
            <div className={`p-4 rounded-lg ${
              saveMessage.includes('Error') 
                ? 'bg-red-50 border border-red-200 text-red-700' 
                : 'bg-green-50 border border-green-200 text-green-700'
            }`}>
              {saveMessage}
            </div>
          )}

          {/* Posting Frequency */}
          <div>
            <div className="flex items-center space-x-2 mb-4">
              <Clock className="h-5 w-5 text-blue-600" />
              <h3 className="text-lg font-semibold text-gray-900">Posting Frequency</h3>
            </div>
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
                  onChange={(e) => setSettings({...settings, postsPerDay: parseInt(e.target.value)})}
                  className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer slider"
                />
                <div className="flex justify-between text-xs text-gray-500 mt-1">
                  <span>1</span>
                  <span>25</span>
                  <span>50</span>
                </div>
              </div>
            </div>
          </div>

          {/* Keywords */}
          <div>
            <div className="flex items-center space-x-2 mb-4">
              <Hash className="h-5 w-5 text-blue-600" />
              <h3 className="text-lg font-semibold text-gray-900">Keywords & Topics</h3>
            </div>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Target Keywords
                </label>
                <div className="flex flex-wrap gap-2 mb-3">
                  {settings.keywords.map((keyword, index) => (
                    <span 
                      key={index}
                      className="inline-flex items-center px-3 py-1 rounded-full text-sm bg-blue-50 text-blue-700"
                    >
                      {keyword}
                      <button 
                        onClick={() => setSettings({
                          ...settings, 
                          keywords: settings.keywords.filter((_, i) => i !== index)
                        })}
                        className="ml-2 hover:text-red-500"
                      >
                        <X className="h-3 w-3" />
                      </button>
                    </span>
                  ))}
                </div>
                <input 
                  type="text"
                  placeholder="Add new keyword..."
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  onKeyPress={(e) => {
                    if (e.key === 'Enter' && e.currentTarget.value.trim()) {
                      setSettings({
                        ...settings,
                        keywords: [...settings.keywords, e.currentTarget.value.trim()]
                      });
                      e.currentTarget.value = '';
                    }
                  }}
                />
              </div>
            </div>
          </div>

          {/* Engagement Mode */}
          <div>
            <div className="flex items-center space-x-2 mb-4">
              <Target className="h-5 w-5 text-blue-600" />
              <h3 className="text-lg font-semibold text-gray-900">Engagement Strategy</h3>
            </div>
            <div className="grid grid-cols-3 gap-4">
              {['conservative', 'balanced', 'aggressive'].map((mode) => (
                <button
                  key={mode}
                  onClick={() => setSettings({...settings, engagementMode: mode})}
                  className={`p-4 rounded-lg border-2 transition-all duration-200 ${
                    settings.engagementMode === mode 
                      ? 'border-blue-500 bg-blue-50' 
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                >
                  <p className="font-medium capitalize">{mode}</p>
                  <p className="text-xs text-gray-600 mt-1">
                    {mode === 'conservative' && 'Low-key posting'}
                    {mode === 'balanced' && 'Moderate activity'}
                    {mode === 'aggressive' && 'High engagement'}
                  </p>
                </button>
              ))}
            </div>
          </div>

          {/* Content Types */}
          <div>
            <div className="flex items-center space-x-2 mb-4">
              <Bot className="h-5 w-5 text-blue-600" />
              <h3 className="text-lg font-semibold text-gray-900">Content Types</h3>
            </div>
            <div className="space-y-3">
              {Object.entries(settings.contentTypes).map(([type, enabled]) => (
                <label key={type} className="flex items-center justify-between">
                  <span className="text-sm font-medium text-gray-700 capitalize">
                    {type.replace(/([A-Z])/g, ' $1').trim()}
                  </span>
                  <input 
                    type="checkbox"
                    checked={enabled}
                    onChange={(e) => setSettings({
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

          {/* Auto Reply */}
          <div>
            <label className="flex items-center justify-between">
              <div>
                <span className="text-sm font-medium text-gray-700">Auto-reply to mentions</span>
                <p className="text-xs text-gray-500">Automatically respond to user interactions</p>
              </div>
              <input 
                type="checkbox"
                checked={settings.autoReply}
                onChange={(e) => setSettings({...settings, autoReply: e.target.checked})}
                className="w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500"
              />
            </label>
          </div>
        </div>
        
        <div className="p-6 border-t border-gray-200">
          <div className="flex space-x-4">
            <button 
              onClick={handleSave}
              disabled={saving}
              className="flex items-center space-x-2 px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors duration-200"
            >
              <Save className="h-4 w-4" />
              <span>{saving ? 'Saving...' : 'Save Settings'}</span>
            </button>
            <button 
              onClick={onClose}
              className="px-6 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors duration-200"
            >
              Cancel
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SettingsModal;