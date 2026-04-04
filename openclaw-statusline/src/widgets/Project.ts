/**
 * Project Widget for OpenClaw Status Line
 * Shows the current project context
 */

export class ProjectWidget {
  private currentProject: string;

  constructor() {
    this.currentProject = this.getCurrentProject();
  }

  async getValue(): Promise<{ label: string; value: string; color: string }> {
    // Update the project in case it changed
    this.currentProject = this.getCurrentProject();
    
    return {
      label: 'Project',
      value: this.currentProject,
      color: '#ff00ff' // Magenta
    };
  }

  private getCurrentProject(): string {
    // In a real implementation, this would get the current project from OpenClaw context
    // For now, we'll try to determine it from the current working directory
    try {
      const path = require('path');
      const cwd = process.cwd();
      const projectName = path.basename(cwd);
      
      // If we're in the OpenClaw workspace, use a recognizable name
      if (cwd.includes('openclaw')) {
        return projectName || 'openclaw-workspace';
      }
      
      return projectName || 'unknown-project';
    } catch (error) {
      return 'current-project';
    }
  }

  // Method to update the current project externally
  setCurrentProject(projectName: string): void {
    this.currentProject = projectName;
  }

  // Get current project
  getCurrentProjectName(): string {
    return this.currentProject;
  }
}