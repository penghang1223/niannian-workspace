"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.GitBranchWidget = void 0;
class GitBranchWidget {
    constructor() {
        this.currentBranch = '';
        this.currentBranch = this.getCurrentBranch();
    }
    async getValue() {
        this.currentBranch = this.getCurrentBranch();
        return {
            label: 'Branch',
            value: this.currentBranch || 'unknown',
            color: '#ffa500'
        };
    }
    getCurrentBranch() {
        try {
            const { execSync } = require('child_process');
            const result = execSync('git rev-parse --abbrev-ref HEAD', {
                encoding: 'utf8',
                stdio: ['pipe', 'pipe', 'ignore']
            });
            return result.trim() || '';
        }
        catch (error) {
            return '';
        }
    }
    refresh() {
        this.currentBranch = this.getCurrentBranch();
    }
    getCurrentBranchName() {
        return this.currentBranch;
    }
}
exports.GitBranchWidget = GitBranchWidget;
//# sourceMappingURL=GitBranch.js.map