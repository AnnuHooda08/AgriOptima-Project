import React from 'react';
import { 
  UserCheck, 
  Leaf, 
  TrendingUp, 
  Store, 
  FileCheck2, 
  SlidersHorizontal,
  LayoutDashboard
} from 'lucide-react';

export default function Navbar({ activeTab, setActiveTab }) {
  const tabs = [
    { id: 'dashboard', label: 'All-in-One Dashboard', icon: LayoutDashboard },
    { id: 'profile', label: '1. Farm Profile', icon: UserCheck },
    { id: 'crop', label: '2. Crop Recommendations', icon: Leaf },
    { id: 'yield', label: '3. Yield & Production', icon: TrendingUp },
    { id: 'market', label: '4. Market & Storage', icon: Store },
    { id: 'plan', label: '5. Final Plan', icon: FileCheck2 },
    { id: 'whatif', label: '6. What-If Analysis', icon: SlidersHorizontal },
  ];

  return (
    <nav className="nav-tabs">
      {tabs.map((tab) => {
        const Icon = tab.icon;
        return (
          <button
            key={tab.id}
            className={`nav-tab ${activeTab === tab.id ? 'active' : ''}`}
            onClick={() => setActiveTab(tab.id)}
          >
            <Icon size={16} />
            {tab.label}
          </button>
        );
      })}
    </nav>
  );
}
