// src/utils/helpers.ts

/**
 * 格式化金额
 */
export function formatCurrency(amount: number, currency: string = 'CNY'): string {
  if (amount < 0) throw new Error('金额不能为负数');
  if (!Number.isFinite(amount)) throw new Error('金额必须是有效数字');
  
  const symbols: Record<string, string> = {
    CNY: '¥',
    USD: '$',
    EUR: '€',
  };
  
  const symbol = symbols[currency] || currency;
  return `${symbol}${amount.toFixed(2)}`;
}

/**
 * 验证邮箱格式
 */
export function validateEmail(email: string): boolean {
  if (!email || typeof email !== 'string') return false;
  const regex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return regex.test(email);
}

/**
 * 生成 URL 友好的 slug
 */
export function generateSlug(title: string): string {
  return title
    .toLowerCase()
    .replace(/[^\w\s-]/g, '')
    .replace(/\s+/g, '-')
    .replace(/-+/g, '-')
    .trim();
}

/**
 * 解析日期字符串
 */
export function parseDate(dateStr: string): Date {
  if (!dateStr || typeof dateStr !== 'string') {
    throw new Error('日期字符串不能为空');
  }
  
  const date = new Date(dateStr);
  if (isNaN(date.getTime())) {
    throw new Error(`无效的日期格式: ${dateStr}`);
  }
  
  return date;
}
