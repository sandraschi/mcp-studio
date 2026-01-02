import React, { useState, useEffect } from 'react';
import { useTheme } from '../contexts/ThemeContext';
import { useToaster } from '../hooks';
import { 
  ArrowLeftIcon,
  SunIcon,
  MoonIcon,
  ComputerDesktopIcon,
  CheckIcon,
  XMarkIcon,
  ArrowPathIcon,
  TrashIcon,
  ExclamationTriangleIcon,
  BellIcon,
  BellSlashIcon,
  ClockIcon,
  ServerStackIcon,
  WrenchIcon,
  CodeBracketIcon,
  UserIcon,
  ShieldCheckIcon,
  DocumentTextIcon,
  InformationCircleIcon
} from '@heroicons/react/24/outline';
import { Button, Card, Tabs, Tab, Switch, Input, Label, Select, Textarea, Badge } from '../components/ui';

export const Settings: React.FC = () => {
  const { theme, setTheme } = useTheme();
  const { success, error } = useToaster();
  const [activeTab, setActiveTab] = useState('appearance');
  const [isSaving, setIsSaving] = useState(false);
  const [isResetting, setIsResetting] = useState(false);
  const [isConfirmingReset, setIsConfirmingReset] = useState(false);
  const [settings, setSettings] = useState({
    appearance: {
      theme: 'system',
      density: 'comfortable',
      fontSize: 'medium',
      showTooltips: true,
      reduceMotion: false,
    },
    notifications: {
      enabled: true,
      sound: true,
      serverStatus: true,
      toolExecution: true,
      updateAvailable: true,
      desktopNotifications: false,
    },
    server: {
      autoStart: true,
      autoDiscover: true,
      discoveryInterval: 30,
      logRetention: 30,
      maxLogSize: 50,
    },
    advanced: {
      enableAnalytics: true,
      enableCrashReporting: true,
      enableTelemetry: true,
      logLevel: 'info',
      apiEndpoint: 'http://localhost:8000/api',
    },
  });

  // Load settings from localStorage on component mount
  useEffect(() => {
    const savedSettings = localStorage.getItem('appSettings');
    if (savedSettings) {
      try {
        setSettings(JSON.parse(savedSettings));
      } catch (err) {
        console.error('Failed to load settings:', err);
      }
    }
  }, []);

  // Save settings to localStorage when they change
  const saveSettings = (newSettings: any) => {
    setSettings(newSettings);
    localStorage.setItem('appSettings', JSON.stringify(newSettings));
  };

  const handleSettingChange = (section: string, key: string, value: any) => {
    const newSettings = {
      ...settings,
      [section]: {
        ...settings[section as keyof typeof settings],
        [key]: value,
      },
    };
    saveSettings(newSettings);
  };

  const handleSave = () => {
    setIsSaving(true);
    // Simulate API call
    setTimeout(() => {
      success('Settings saved successfully');
      setIsSaving(false);
    }, 1000);
  };

  const handleReset = () => {
    if (!isConfirmingReset) {
      setIsConfirmingReset(true);
      setTimeout(() => setIsConfirmingReset(false), 3000);
      return;
    }

    setIsResetting(true);
    // Simulate reset
    setTimeout(() => {
      const defaultSettings = {
        appearance: {
          theme: 'system',
          density: 'comfortable',
          fontSize: 'medium',
          showTooltips: true,
          reduceMotion: false,
        },
        notifications: {
          enabled: true,
          sound: true,
          serverStatus: true,
          toolExecution: true,
          updateAvailable: true,
          desktopNotifications: false,
        },
        server: {
          autoStart: true,
          autoDiscover: true,
          discoveryInterval: 30,
          logRetention: 30,
          maxLogSize: 50,
        },
        advanced: {
          enableAnalytics: true,
          enableCrashReporting: true,
          enableTelemetry: true,
          logLevel: 'info',
          apiEndpoint: 'http://localhost:8000/api',
        },
      };
      
      saveSettings(defaultSettings);
      setTheme('system');
      success('Settings reset to default');
      setIsResetting(false);
      setIsConfirmingReset(false);
    }, 1000);
  };

  const renderAppearanceSettings = () => (
    <div className="space-y-6">
      <div>
        <Label>Theme</Label>
        <div className="mt-2 grid grid-cols-1 gap-4 sm:grid-cols-3">
          {[
            { value: 'light', label: 'Light', icon: SunIcon },
            { value: 'dark', label: 'Dark', icon: MoonIcon },
            { value: 'system', label: 'System', icon: ComputerDesktopIcon },
          ].map((option) => (
            <button
              key={option.value}
              type="button"
              onClick={() => {
                handleSettingChange('appearance', 'theme', option.value);
                setTheme(option.value as 'light' | 'dark' | 'system');
              }}
              className={`relative flex items-center justify-center rounded-lg border p-4 focus:outline-none ${
                settings.appearance.theme === option.value
                  ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/30 ring-2 ring-blue-500'
                  : 'border-gray-300 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-700'
              }`}
            >
              <div className="flex flex-col items-center">
                <option.icon className="h-6 w-6 mb-2" />
                <span className="text-sm font-medium text-gray-900 dark:text-white">
                  {option.label}
                </span>
              </div>
              {settings.appearance.theme === option.value && (
                <div className="absolute top-2 right-2 flex h-5 w-5 items-center justify-center rounded-full bg-blue-500 text-white">
                  <CheckIcon className="h-3 w-3" />
                </div>
              )}
            </button>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-1 gap-6 sm:grid-cols-2">
        <div>
          <Label>Density</Label>
          <Select
            value={settings.appearance.density}
            onChange={(e) => handleSettingChange('appearance', 'density', e.target.value)}
            className="mt-1"
          >
            <option value="compact">Compact</option>
            <option value="comfortable">Comfortable</option>
            <option value="spacious">Spacious</option>
          </Select>
        </div>

        <div>
          <Label>Font Size</Label>
          <Select
            value={settings.appearance.fontSize}
            onChange={(e) => handleSettingChange('appearance', 'fontSize', e.target.value)}
            className="mt-1"
          >
            <option value="small">Small</option>
            <option value="medium">Medium</option>
            <option value="large">Large</option>
          </Select>
        </div>
      </div>

      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <Label>Show Tooltips</Label>
            <p className="text-sm text-gray-500 dark:text-gray-400">
              Display helpful tooltips and hints throughout the application
            </p>
          </div>
          <Switch
            checked={settings.appearance.showTooltips}
            onChange={(checked) => handleSettingChange('appearance', 'showTooltips', checked)}
          />
        </div>

        <div className="flex items-center justify-between">
          <div>
            <Label>Reduce Motion</Label>
            <p className="text-sm text-gray-500 dark:text-gray-400">
              Disable animations and transitions for better performance
            </p>
          </div>
          <Switch
            checked={settings.appearance.reduceMotion}
            onChange={(checked) => handleSettingChange('appearance', 'reduceMotion', checked)}
          />
        </div>
      </div>
    </div>
  );

  const renderNotificationSettings = () => (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <Label>Enable Notifications</Label>
          <p className="text-sm text-gray-500 dark:text-gray-400">
            Receive notifications for important events
          </p>
        </div>
        <Switch
          checked={settings.notifications.enabled}
          onChange={(checked) => handleSettingChange('notifications', 'enabled', checked)}
        />
      </div>

      <div className="space-y-4">
        <h4 className="text-sm font-medium text-gray-900 dark:text-white">Notification Types</h4>
        
        <div className="flex items-center justify-between">
          <div>
            <Label>Server Status Changes</Label>
            <p className="text-sm text-gray-500 dark:text-gray-400">
              When servers go online/offline or encounter errors
            </p>
          </div>
          <Switch
            checked={settings.notifications.serverStatus}
            onChange={(checked) => handleSettingChange('notifications', 'serverStatus', checked)}
            disabled={!settings.notifications.enabled}
          />
        </div>

        <div className="flex items-center justify-between">
          <div>
            <Label>Tool Execution</Label>
            <p className="text-sm text-gray-500 dark:text-gray-400">
              When tools complete execution or encounter errors
            </p>
          </div>
          <Switch
            checked={settings.notifications.toolExecution}
            onChange={(checked) => handleSettingChange('notifications', 'toolExecution', checked)}
            disabled={!settings.notifications.enabled}
          />
        </div>

        <div className="flex items-center justify-between">
          <div>
            <Label>Update Available</Label>
            <p className="text-sm text-gray-500 dark:text-gray-400">
              When a new version of the application is available
            </p>
          </div>
          <Switch
            checked={settings.notifications.updateAvailable}
            onChange={(checked) => handleSettingChange('notifications', 'updateAvailable', checked)}
            disabled={!settings.notifications.enabled}
          />
        </div>
      </div>

      <div className="space-y-4 pt-4 border-t border-gray-200 dark:border-gray-700">
        <div className="flex items-center justify-between">
          <div>
            <Label>Enable Sound</Label>
            <p className="text-sm text-gray-500 dark:text-gray-400">
              Play sounds for notifications
            </p>
          </div>
          <Switch
            checked={settings.notifications.sound}
            onChange={(checked) => handleSettingChange('notifications', 'sound', checked)}
            disabled={!settings.notifications.enabled}
          />
        </div>

        <div className="flex items-center justify-between">
          <div>
            <Label>Desktop Notifications</Label>
            <p className="text-sm text-gray-500 dark:text-gray-400">
              Show notifications in your operating system's notification center
            </p>
          </div>
          <Switch
            checked={settings.notifications.desktopNotifications}
            onChange={(checked) => handleSettingChange('notifications', 'desktopNotifications', checked)}
            disabled={!settings.notifications.enabled}
          />
        </div>
      </div>
    </div>
  );

  const renderServerSettings = () => (
    <div className="space-y-6">
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <Label>Auto-start Servers</Label>
            <p className="text-sm text-gray-500 dark:text-gray-400">
              Automatically start servers when the application launches
            </p>
          </div>
          <Switch
            checked={settings.server.autoStart}
            onChange={(checked) => handleSettingChange('server', 'autoStart', checked)}
          />
        </div>

        <div className="flex items-center justify-between">
          <div>
            <Label>Auto-discover Servers</Label>
            <p className="text-sm text-gray-500 dark:text-gray-400">
              Automatically discover and add MCP servers from your system
            </p>
          </div>
          <Switch
            checked={settings.server.autoDiscover}
            onChange={(checked) => handleSettingChange('server', 'autoDiscover', checked)}
          />
        </div>
      </div>

      <div className="grid grid-cols-1 gap-6 sm:grid-cols-2">
        <div>
          <Label>Discovery Interval (seconds)</Label>
          <Input
            type="number"
            min="5"
            max="3600"
            value={settings.server.discoveryInterval}
            onChange={(e) => handleSettingChange('server', 'discoveryInterval', parseInt(e.target.value))}
            className="mt-1"
            disabled={!settings.server.autoDiscover}
          />
        </div>

        <div>
          <Label>Log Retention (days)</Label>
          <Input
            type="number"
            min="1"
            max="365"
            value={settings.server.logRetention}
            onChange={(e) => handleSettingChange('server', 'logRetention', parseInt(e.target.value))}
            className="mt-1"
          />
        </div>

        <div>
          <Label>Max Log Size (MB)</Label>
          <Input
            type="number"
            min="1"
            max="1024"
            value={settings.server.maxLogSize}
            onChange={(e) => handleSettingChange('server', 'maxLogSize', parseInt(e.target.value))}
            className="mt-1"
          />
        </div>
      </div>
    </div>
  );

  const renderAdvancedSettings = () => (
    <div className="space-y-6">
      <div>
        <Label>API Endpoint</Label>
        <Input
          type="url"
          value={settings.advanced.apiEndpoint}
          onChange={(e) => handleSettingChange('advanced', 'apiEndpoint', e.target.value)}
          className="mt-1 font-mono text-sm"
        />
        <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
          URL of the MCP Studio API server
        </p>
      </div>

      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <Label>Enable Analytics</Label>
            <p className="text-sm text-gray-500 dark:text-gray-400">
              Help improve MCP Studio by sending anonymous usage data
            </p>
          </div>
          <Switch
            checked={settings.advanced.enableAnalytics}
            onChange={(checked) => handleSettingChange('advanced', 'enableAnalytics', checked)}
          />
        </div>

        <div className="flex items-center justify-between">
          <div>
            <Label>Enable Crash Reporting</Label>
            <p className="text-sm text-gray-500 dark:text-gray-400">
              Automatically send crash reports to help fix issues
            </p>
          </div>
          <Switch
            checked={settings.advanced.enableCrashReporting}
            onChange={(checked) => handleSettingChange('advanced', 'enableCrashReporting', checked)}
          />
        </div>

        <div className="flex items-center justify-between">
          <div>
            <Label>Enable Telemetry</Label>
            <p className="text-sm text-gray-500 dark:text-gray-400">
              Send anonymous usage statistics to improve the application
            </p>
          </div>
          <Switch
            checked={settings.advanced.enableTelemetry}
            onChange={(checked) => handleSettingChange('advanced', 'enableTelemetry', checked)}
          />
        </div>
      </div>

      <div>
        <Label>Log Level</Label>
        <Select
          value={settings.advanced.logLevel}
          onChange={(e) => handleSettingChange('advanced', 'logLevel', e.target.value)}
          className="mt-1"
        >
          <option value="error">Error</option>
          <option value="warn">Warning</option>
          <option value="info">Info</option>
          <option value="debug">Debug</option>
          <option value="trace">Trace</option>
        </Select>
      </div>
    </div>
  );

  const renderAboutSettings = () => (
    <div className="space-y-6">
      <div className="bg-white dark:bg-gray-800 shadow overflow-hidden sm:rounded-lg">
        <div className="px-4 py-5 sm:px-6">
          <h3 className="text-lg leading-6 font-medium text-gray-900 dark:text-white">
            MCP Studio
          </h3>
          <p className="mt-1 max-w-2xl text-sm text-gray-500 dark:text-gray-400">
            A modern interface for managing MCP servers and tools
          </p>
        </div>
        <div className="border-t border-gray-200 dark:border-gray-700">
          <dl>
            <div className="bg-gray-50 dark:bg-gray-700 px-4 py-5 sm:grid sm:grid-cols-3 sm:gap-4 sm:px-6">
              <dt className="text-sm font-medium text-gray-500 dark:text-gray-300">Version</dt>
              <dd className="mt-1 text-sm text-gray-900 dark:text-white sm:mt-0 sm:col-span-2">
                1.0.0
              </dd>
            </div>
            <div className="bg-white dark:bg-gray-800 px-4 py-5 sm:grid sm:grid-cols-3 sm:gap-4 sm:px-6">
              <dt className="text-sm font-medium text-gray-500 dark:text-gray-300">License</dt>
              <dd className="mt-1 text-sm text-gray-900 dark:text-white sm:mt-0 sm:col-span-2">
                MIT
              </dd>
            </div>
            <div className="bg-gray-50 dark:bg-gray-700 px-4 py-5 sm:grid sm:grid-cols-3 sm:gap-4 sm:px-6">
              <dt className="text-sm font-medium text-gray-500 dark:text-gray-300">Documentation</dt>
              <dd className="mt-1 text-sm text-blue-600 dark:text-blue-400 hover:text-blue-500 dark:hover:text-blue-300 sm:mt-0 sm:col-span-2">
                <a href="#" className="flex items-center">
                  <DocumentTextIcon className="h-4 w-4 mr-1" />
                  View Documentation
                </a>
              </dd>
            </div>
            <div className="bg-white dark:bg-gray-800 px-4 py-5 sm:grid sm:grid-cols-3 sm:gap-4 sm:px-6">
              <dt className="text-sm font-medium text-gray-500 dark:text-gray-300">GitHub</dt>
              <dd className="mt-1 text-sm text-blue-600 dark:text-blue-400 hover:text-blue-500 dark:hover:text-blue-300 sm:mt-0 sm:col-span-2">
                <a href="#" className="flex items-center">
                  <CodeBracketIcon className="h-4 w-4 mr-1" />
                  github.com/your-org/mcp-studio
                </a>
              </dd>
            </div>
            <div className="bg-gray-50 dark:bg-gray-700 px-4 py-5 sm:grid sm:grid-cols-3 sm:gap-4 sm:px-6">
              <dt className="text-sm font-medium text-gray-500 dark:text-gray-300">Report an Issue</dt>
              <dd className="mt-1 text-sm text-blue-600 dark:text-blue-400 hover:text-blue-500 dark:hover:text-blue-300 sm:mt-0 sm:col-span-2">
                <a href="#" className="flex items-center">
                  <ExclamationTriangleIcon className="h-4 w-4 mr-1" />
                  Open GitHub Issue
                </a>
              </dd>
            </div>
          </dl>
        </div>
      </div>

      <div className="bg-white dark:bg-gray-800 shadow sm:rounded-lg">
        <div className="px-4 py-5 sm:p-6">
          <h3 className="text-lg leading-6 font-medium text-gray-900 dark:text-white">
            System Information
          </h3>
          <div className="mt-2 max-w-xl text-sm text-gray-500 dark:text-gray-400">
            <p>View system information and diagnostic data for troubleshooting.</p>
          </div>
          <div className="mt-5">
            <Button variant="secondary">
              <DocumentTextIcon className="h-4 w-4 mr-2" />
              Export System Report
            </Button>
          </div>
        </div>
      </div>
    </div>
  );

  return (
    <div className="space-y-6">
      <div className="md:flex md:items-center md:justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white">Settings</h2>
          <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
            Manage your application settings and preferences
          </p>
        </div>
        <div className="mt-4 flex space-x-3 md:mt-0">
          <Button
            variant="danger"
            onClick={handleReset}
            disabled={isResetting}
          >
            {isResetting ? (
              <>
                <ArrowPathIcon className="animate-spin -ml-1 mr-2 h-4 w-4" />
                Resetting...
              </>
            ) : isConfirmingReset ? (
              'Click again to confirm'
            ) : (
              <>
                <TrashIcon className="-ml-1 mr-2 h-4 w-4" />
                Reset to Defaults
              </>
            )}
          </Button>
          <Button
            onClick={handleSave}
            disabled={isSaving}
          >
            {isSaving ? (
              <>
                <ArrowPathIcon className="animate-spin -ml-1 mr-2 h-4 w-4" />
                Saving...
              </>
            ) : (
              'Save Changes'
            )}
          </Button>
        </div>
      </div>

      <Card>
        <Tabs value={activeTab} onChange={setActiveTab}>
          <Tab value="appearance" icon={<SunIcon className="h-5 w-5" />}>
            Appearance
          </Tab>
          <Tab value="notifications" icon={<BellIcon className="h-5 w-5" />}>
            Notifications
          </Tab>
          <Tab value="server" icon={<ServerStackIcon className="h-5 w-5" />}>
            Server
          </Tab>
          <Tab value="advanced" icon={<WrenchIcon className="h-5 w-5" />}>
            Advanced
          </Tab>
          <Tab value="about" icon={<InformationCircleIcon className="h-5 w-5" />}>
            About
          </Tab>
        </Tabs>

        <div className="mt-6">
          {activeTab === 'appearance' && renderAppearanceSettings()}
          {activeTab === 'notifications' && renderNotificationSettings()}
          {activeTab === 'server' && renderServerSettings()}
          {activeTab === 'advanced' && renderAdvancedSettings()}
          {activeTab === 'about' && renderAboutSettings()}
        </div>
      </Card>
    </div>
  );
};
