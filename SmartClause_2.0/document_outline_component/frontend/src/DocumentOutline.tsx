import React, { useEffect, useCallback } from "react";
import {
  Streamlit,
  StreamlitComponentBase,
  withStreamlitConnection,
} from "streamlit-component-lib";
import "./DocumentOutline.css";

interface Heading {
  level: number;
  text: string;
  id: string;
}

interface State {
  prevHeight?: number;
}

class DocumentOutline extends StreamlitComponentBase<State> {
  public state: State = {};

  public componentDidMount(): void {
    const height = this.props.args["height"] || 800;
    Streamlit.setFrameHeight(height);
  }

  public componentDidUpdate(): void {
    const currentHeight = this.props.args["height"] || 800;
    const prevHeight = this.state.prevHeight || 800;
    
    if (currentHeight !== prevHeight) {
      this.setState({ prevHeight: currentHeight });
      Streamlit.setFrameHeight(currentHeight);
    }
  }

  private handleHeadingClick = (id: string): void => {
    Streamlit.setComponentValue(id);
  };

  private getPadding = (level: number): string => {
    const basePadding = 16;
    return `${Math.max(0, level - 1) * basePadding}px`;
  };

  public render = (): React.ReactNode => {
    const headings: Heading[] = this.props.args["headings"] || [];
    const height = this.props.args["height"] || 800;

    return (
      <div className="outline-container" style={{ height: `${height}px` }}>
        <div className="outline-header">Document Outline</div>
        <div className="outline-list">
          {headings.length === 0 ? (
            <div className="empty-state">
              No headings found in the document.
            </div>
          ) : (
            headings.map((heading: Heading, index: number) => (
              <div
                key={`${heading.id}-${index}`}
                className={`outline-item level-${heading.level}`}
                style={{ paddingLeft: this.getPadding(heading.level) }}
                onClick={() => this.handleHeadingClick(heading.id)}
              >
                {heading.text}
              </div>
            ))
          )}
        </div>
      </div>
    );
  };
}

export default withStreamlitConnection(DocumentOutline);