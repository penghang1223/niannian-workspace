/**
 * Cost Tracking Widget for OpenClaw Status Line
 * Shows estimated costs for the current session
 */

export class CostWidget {
  private sessionCost: number = 0;
  private startTime: number;

  constructor() {
    this.startTime = Date.now();
    this.initializeCostTracking();
  }

  private initializeCostTracking(): void {
    // In a real implementation, this would track actual API costs
    // For now, we'll simulate cost accumulation
    setInterval(() => {
      // Simulate cost accumulation - add random small amounts to demonstrate
      const costIncrease = Math.random() * 0.0005; // Small increments to simulate API costs
      this.sessionCost += costIncrease;
    }, 10000); // Update every 10 seconds
  }

  async getValue(): Promise<{ label: string; value: string; color: string }> {
    return {
      label: 'Cost',
      value: `$${this.sessionCost.toFixed(6)}`,
      color: '#00ffff' // Cyan
    };
  }

  // Method to update cost externally
  updateCost(newCost: number): void {
    this.sessionCost = newCost;
  }

  // Get current cost
  getCost(): number {
    return this.sessionCost;
  }

  // Reset the session cost
  resetCost(): void {
    this.sessionCost = 0;
    this.startTime = Date.now();
  }
}