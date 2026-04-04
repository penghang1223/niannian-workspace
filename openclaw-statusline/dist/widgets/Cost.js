"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.CostWidget = void 0;
class CostWidget {
    constructor() {
        this.sessionCost = 0;
        this.startTime = Date.now();
        this.initializeCostTracking();
    }
    initializeCostTracking() {
        setInterval(() => {
            const costIncrease = Math.random() * 0.0005;
            this.sessionCost += costIncrease;
        }, 10000);
    }
    async getValue() {
        return {
            label: 'Cost',
            value: `$${this.sessionCost.toFixed(6)}`,
            color: '#00ffff'
        };
    }
    updateCost(newCost) {
        this.sessionCost = newCost;
    }
    getCost() {
        return this.sessionCost;
    }
    resetCost() {
        this.sessionCost = 0;
        this.startTime = Date.now();
    }
}
exports.CostWidget = CostWidget;
//# sourceMappingURL=Cost.js.map