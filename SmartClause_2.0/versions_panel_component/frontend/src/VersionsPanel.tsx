import React, { useState, useEffect, useCallback } from "react";
import { withStreamlitConnection, Streamlit, ComponentProps } from "streamlit-component-lib";

// Define the shape of a Version object passed from Python
interface Version {
  id: string;
  label: string;
  timestamp: string; // Expecting ISO string
  is_major_version: boolean;
  change_summary?: string;
}

// Helper function to format date/time
const formatTimeAgo = (isoDate: string): string => {
  const now = new Date();
  const past = new Date(isoDate);
  const diffInSeconds = Math.floor((now.getTime() - past.getTime()) / 1000);

  if (diffInSeconds < 60) return "Just now";
  if (diffInSeconds < 3600) return `${Math.floor(diffInSeconds / 60)}m ago`;
  if (diffInSeconds < 86400) return `${Math.floor(diffInSeconds / 3600)}h ago`;
  if (diffInSeconds < 2592000) return `${Math.floor(diffInSeconds / 86400)}d ago`;
  
  return past.toLocaleDateString("en-US", { month: "short", day: "numeric" });
};

const VersionsPanel: React.FC<ComponentProps> = (props: ComponentProps) => {
  // Get props passed from Python
  const args = props.args;
  const versionsProp: Version[] = args["versions"] || [];
  const currentVersionIdProp: string = args["currentVersionId"] || "";

  // State to track which item is visually selected
  const [selectedVersionId, setSelectedVersionId] = useState<string>(currentVersionIdProp);

  // Update selection if the current ID from Python changes
  useEffect(() => {
    setSelectedVersionId(currentVersionIdProp);
  }, [currentVersionIdProp]);

  // Handle click on a version item
  const handleSelectVersion = useCallback((id: string) => {
    if (id !== selectedVersionId) {
      setSelectedVersionId(id);
      // Send the selected ID back to Streamlit
      Streamlit.setComponentValue(id);
    }
  }, [selectedVersionId]);
  
  // Tell Streamlit to set the component's height to 500px
  useEffect(() => {
    Streamlit.setFrameHeight(500);
  }, []);

  // Sort versions to show newest first
  const sortedVersions = [...versionsProp].sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime());
  
  return (
    <div className="versions-panel-container" style={{ height: '500px' }}>
      <div className="panel-header">
        {/* Icon */}
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 22h6a2 2 0 0 0 2-2V7l-5-5H6a2 2 0 0 0-2 2v10"/><path d="M14 2v4a2 2 0 0 0 2 2h4"/><path d="M2 17h10"/></svg>
        <h2 className="panel-title">Document Versions</h2>
      </div>
      
      <div className="versions-list">
        {sortedVersions.length === 0 ? (
          <div className="version-item empty-state">No versions saved yet.</div>
        ) : (
          sortedVersions.map((version) => {
            const isActive = version.id === currentVersionIdProp;
            const isSelected = version.id === selectedVersionId;
            
            return (
              <div
                key={version.id}
                className={`version-item ${isSelected ? "selected" : ""} ${isActive ? "active-current" : ""}`}
                onClick={() => handleSelectVersion(version.id)}
              >
                <div className="version-details">
                  <div className="version-title-row">
                    <span className="version-label">
                        {version.label}
                        {isActive && <span className="current-badge">ACTIVE</span>}
                    </span>
                    <span className="version-time">{formatTimeAgo(version.timestamp)}</span>
                  </div>
                  {version.change_summary && (
                    <p className="version-summary">
                        {version.change_summary}
                    </p>
                  )}
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};

export default withStreamlitConnection(VersionsPanel);