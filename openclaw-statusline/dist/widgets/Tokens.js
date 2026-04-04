"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.TokenWidget = void 0;
class TokenWidget {
    constructor() {
        this.tokenCount = 0;
        this.startTime = Date.now();
        this.initializeTokenTracking();
    }
    initializeTokenTracking() {
        setInterval(() => {
            this.tokenCount += Math.floor(Math.random() * 10) + 1;
        }, 5000);
    }
    async getValue() {
        return {
            label: 'Tokens',
            value: this.formatTokenCount(this.tokenCount),
            color: '#00ff00'
        };
    }
    formatTokenCount(count) {
        if (count >= 1000000) {
            return `${(count / 1000000).toFixed(1)}M`;
        }
        else if (count >= 1000) {
            return `${(count / 1000).toFixed(1)}K`;
        }
        else {
            return count.toString();
        }
    }
    updateTokenCount(newCount) {
        this.tokenCount = newCount;
    }
    getTokenCount() {
        return this.tokenCount;
    }
}
exports.TokenWidget = TokenWidget;
//# sourceMappingURL=Tokens.js.map