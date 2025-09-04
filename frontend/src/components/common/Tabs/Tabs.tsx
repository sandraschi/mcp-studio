import React, { Children, ReactElement, cloneElement, useState, useEffect } from 'react';
import { classNames } from '../../../utils/classNames';

interface TabsProps {
  children: React.ReactNode;
  selectedTab?: string;
  onChange?: (tabId: string) => void;
  className?: string;
}

export const Tabs: React.FC<TabsProps> & {
  TabList: typeof TabList;
  Tab: typeof Tab;
  TabPanel: typeof TabPanel;
} = ({ children, selectedTab, onChange, className = '' }) => {
  const [activeTab, setActiveTab] = useState<string>('');
  const [tabs, setTabs] = useState<Array<{ id: string; label: string }>>([]);
  const [panels, setPanels] = useState<Array<{ id: string; children: React.ReactNode }>>([]);

  // Process children to separate TabList and TabPanels
  useEffect(() => {
    let tabList: ReactElement | null = null;
    const tabPanels: ReactElement[] = [];
    
    Children.forEach(children, (child) => {
      if (!React.isValidElement(child)) return;
      
      if (child.type === TabList) {
        tabList = child;
      } else if (child.type === TabPanel) {
        tabPanels.push(child);
      }
    });

    // Extract tab information from TabList
    if (tabList) {
      const tabElements = Children.toArray(tabList.props.children).filter(
        (child) => React.isValidElement(child) && child.type === Tab
      ) as ReactElement[];
      
      const tabData = tabElements.map((tab) => ({
        id: tab.props.id,
        label: tab.props.children,
      }));
      
      setTabs(tabData);
      
      // Set initial active tab if not provided
      if (tabData.length > 0 && !activeTab) {
        const initialTab = selectedTab || tabData[0].id;
        setActiveTab(initialTab);
      }
    }

    // Process panels
    const panelData = tabPanels.map((panel) => ({
      id: panel.props.id,
      children: panel.props.children,
    }));
    
    setPanels(panelData);
  }, [children, selectedTab]);

  // Handle tab change
  const handleTabChange = (tabId: string) => {
    setActiveTab(tabId);
    if (onChange) {
      onChange(tabId);
    }
  };

  // Update active tab when selectedTab prop changes
  useEffect(() => {
    if (selectedTab) {
      setActiveTab(selectedTab);
    }
  }, [selectedTab]);

  return (
    <div className={classNames('tabs', className)}>
      {tabs.length > 0 && (
        <TabList>
          {tabs.map((tab) => (
            <Tab
              key={tab.id}
              id={tab.id}
              active={activeTab === tab.id}
              onClick={() => handleTabChange(tab.id)}
            >
              {tab.label}
            </Tab>
          ))}
        </TabList>
      )}
      
      {panels.map((panel) => (
        <TabPanel 
          key={panel.id} 
          id={panel.id} 
          isActive={activeTab === panel.id}
        >
          {panel.children}
        </TabPanel>
      ))}
    </div>
  );
};

// TabList Component
interface TabListProps {
  children: React.ReactNode;
  className?: string;
}

export const TabList: React.FC<TabListProps> = ({ 
  children, 
  className = '' 
}) => {
  return (
    <div className={classNames('border-b border-gray-200 dark:border-gray-700', className)}>
      <nav className="-mb-px flex space-x-8" aria-label="Tabs">
        {children}
      </nav>
    </div>
  );
};

// Tab Component
interface TabProps {
  id: string;
  children: React.ReactNode;
  active?: boolean;
  onClick?: () => void;
  className?: string;
}

export const Tab: React.FC<TabProps> = ({ 
  id, 
  children, 
  active = false, 
  onClick, 
  className = '' 
}) => {
  return (
    <button
      id={`tab-${id}`}
      role="tab"
      aria-selected={active}
      aria-controls={`panel-${id}`}
      onClick={onClick}
      className={classNames(
        'py-4 px-1 border-b-2 font-medium text-sm',
        active
          ? 'border-blue-500 text-blue-600 dark:border-blue-400 dark:text-blue-300'
          : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300 dark:text-gray-400 dark:hover:text-gray-200',
        'whitespace-nowrap',
        className
      )}
    >
      {children}
    </button>
  );
};

// TabPanel Component
interface TabPanelProps {
  id: string;
  children: React.ReactNode;
  isActive?: boolean;
  className?: string;
}

export const TabPanel: React.FC<TabPanelProps> = ({ 
  id, 
  children, 
  isActive = false, 
  className = '' 
}) => {
  return (
    <div
      id={`panel-${id}`}
      role="tabpanel"
      aria-labelledby={`tab-${id}`}
      className={classNames(!isActive && 'hidden', className)}
    >
      {children}
    </div>
  );
};

// Set up compound components
Tabs.TabList = TabList;
Tabs.Tab = Tab;
Tabs.TabPanel = TabPanel;
