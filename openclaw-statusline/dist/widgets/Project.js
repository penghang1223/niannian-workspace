"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.ProjectWidget = void 0;
class ProjectWidget {
    constructor() {
        this.currentProject = this.getCurrentProject();
    }
    async getValue() {
        this.currentProject = this.getCurrentProject();
        return {
            label: 'Project',
            value: this.currentProject,
            color: '#ff00ff'
        };
    }
    getCurrentProject() {
        try {
            const path = require('path');
            const cwd = process.cwd();
            const projectName = path.basename(cwd);
            if (cwd.includes('openclaw')) {
                return projectName || 'openclaw-workspace';
            }
            return projectName || 'unknown-project';
        }
        catch (error) {
            return 'current-project';
        }
    }
    setCurrentProject(projectName) {
        this.currentProject = projectName;
    }
    getCurrentProjectName() {
        return this.currentProject;
    }
}
exports.ProjectWidget = ProjectWidget;
//# sourceMappingURL=Project.js.map