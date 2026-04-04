/**
 * Git Branch Widget for OpenClaw Status Line
 * Shows the current git branch
 */

export class GitBranchWidget {
  private currentBranch: string = '';

  constructor() {
    this.currentBranch = this.getCurrentBranch();
  }

  async getValue(): Promise<{ label: string; value: string; color: string }> {
    // Refresh the branch in case it changed
    this.currentBranch = this.getCurrentBranch();
    
    return {
      label: 'Branch',
      value: this.currentBranch || 'unknown',
      color: '#ffa500' // Orange
    };
  }

  private getCurrentBranch(): string {
    try {
      const { execSync } = require('child_process');
      const result = execSync('git rev-parse --abbrev-ref HEAD', { 
        encoding: 'utf8', 
        stdio: ['pipe', 'pipe', 'ignore'] 
      });
      return result.trim() || '';
    } catch (error) {
      // If git command fails, return empty string
      return '';
    }
  }

  // Method to manually refresh the branch
  refresh(): void {
    this.currentBranch = this.getCurrentBranch();
  }

  // Get current branch
  getCurrentBranchName(): string {
    return this.currentBranch;
  }
}