/**
 * Session Clock Widget for OpenClaw Status Line
 * Shows the duration of the current session
 */

export class SessionClockWidget {
  private startTime: number;

  constructor() {
    this.startTime = Date.now();
  }

  async getValue(): Promise<{ label: string; value: string; color: string }> {
    const elapsed = Date.now() - this.startTime;
    const formattedTime = this.formatElapsedTime(elapsed);
    
    return {
      label: 'Session',
      value: formattedTime,
      color: '#ffff00' // Yellow
    };
  }

  private formatElapsedTime(ms: number): string {
    const seconds = Math.floor(ms / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);
    
    if (hours > 0) {
      return `${hours}h ${minutes % 60}m ${seconds % 60}s`;
    } else if (minutes > 0) {
      return `${minutes}m ${seconds % 60}s`;
    } else {
      return `${seconds}s`;
    }
  }

  // Reset the session timer
  reset(): void {
    this.startTime = Date.now();
  }

  // Get current elapsed time in ms
  getElapsedTime(): number {
    return Date.now() - this.startTime;
  }
}