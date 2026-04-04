"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.Renderer = void 0;
class Renderer {
    constructor(config) {
        this.config = config;
    }
    render(widgets) {
        const separator = this.config.get('separator', ' | ');
        const position = this.config.get('position', 'bottom');
        const formattedWidgets = widgets.map(widget => {
            const color = widget.color || this.config.get(`colors.${widget.label.toLowerCase()}`, '#ffffff');
            return this.applyColor(`${widget.label}: ${widget.value}`, color);
        });
        const statusLine = formattedWidgets.join(separator);
        if (position === 'top') {
            return `┌─${'─'.repeat(process.stdout.columns - 4)}─┐\n│ ${statusLine} │\n└─${'─'.repeat(process.stdout.columns - 4)}─┘`;
        }
        else {
            return statusLine;
        }
    }
    applyColor(text, color) {
        const colorMap = {
            '#00ff00': '\x1b[32m',
            '#ffff00': '\x1b[33m',
            '#ff00ff': '\x1b[35m',
            '#00ffff': '\x1b[36m',
            '#ffa500': '\x1b[38;5;208m',
            '#ff0000': '\x1b[31m',
            '#800080': '\x1b[38;5;93m',
            '#ffffff': '\x1b[37m'
        };
        const resetCode = '\x1b[0m';
        const colorCode = colorMap[color] || '\x1b[37m';
        return `${colorCode}${text}${resetCode}`;
    }
}
exports.Renderer = Renderer;
//# sourceMappingURL=renderer.js.map