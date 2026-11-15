import { Component, type ErrorInfo, type ReactNode } from "react";
import { Link } from "react-router-dom";

interface ErrorBoundaryState {
  hasError: boolean;
}

export default class ErrorBoundary extends Component<{ children: ReactNode }, ErrorBoundaryState> {
  state: ErrorBoundaryState = { hasError: false };

  static getDerivedStateFromError(): ErrorBoundaryState {
    return { hasError: true };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error("ZYNTARA interface rendering failed.", error, info.componentStack);
  }

  render() {
    if (this.state.hasError) {
      return (
        <main className="fatal-error">
          <span className="eyebrow">INTERFACE ERROR</span>
          <h1>Research workspace unavailable.</h1>
          <p>An unexpected rendering error interrupted this view.</p>
          <div><button className="primary-button" onClick={() => window.location.reload()}>RELOAD WORKSPACE</button><Link to="/">RETURN TO MISSION</Link></div>
        </main>
      );
    }

    return this.props.children;
  }
}
