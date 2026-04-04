"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.SessionClockWidget = void 0;
class SessionClockWidget {
    constructor() {
        this.startTime = Date.now();
    }
    async getValue() {
        const elapsed = Date.now() - this.startTime;
        const formattedTime = this.formatElapsedTime(elapsed);
        return {
            label: 'Session',
            value: formattedTime,
            color: '#ffff00'
        };
    }
    formatElapsedTime(ms) {
        const seconds = Math.floor(ms / 1000);
        const minutes = Math.floor(seconds / 60);
        const hours = Math.floor(minutes / 60);
        if (hours > 0) {
            return `${hours}h ${minutes % 60}m ${seconds % 60}s`;
        }
        else if (minutes > 0) {
            return `${minutes}m ${seconds % 60}s`;
        }
        else {
            return `${seconds}s`;
        }
    }
    reset() {
        this.startTime = Date.now();
    }
    getElapsedTime() {
        return Date.now() - this.startTime;
    }
}
exports.SessionClockWidget = SessionClockWidget;
//# sourceMappingURL=SessionClock.js.map