import { Component } from 'react';
import { ErrorState } from './UI';

export default class WorkspaceErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false };
    this.handleRetry = this.handleRetry.bind(this);
  }

  static getDerivedStateFromError() {
    return { hasError: true };
  }

  componentDidUpdate(previousProps) {
    if (this.state.hasError && previousProps.resetKey !== this.props.resetKey) {
      this.setState({ hasError: false });
    }
  }

  handleRetry() {
    this.setState({ hasError: false });
    this.props.onRecover();
  }

  render() {
    if (this.state.hasError) {
      return <div className="workspace-page"><ErrorState title="This workspace step could not be displayed" message="No candidate data was lost. Return to Evidence and continue from the last saved step." onRetry={this.handleRetry} retryLabel="Return to Evidence" /></div>;
    }
    return this.props.children;
  }
}
