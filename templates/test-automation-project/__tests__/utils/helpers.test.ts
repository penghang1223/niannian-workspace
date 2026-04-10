// __tests__/utils/helpers.test.ts

import { formatCurrency, validateEmail, generateSlug, parseDate } from '../../src/utils/helpers';

describe('工具函数测试', () => {
  
  describe('formatCurrency', () => {
    it('应该返回人民币格式当不指定货币时', () => {
      expect(formatCurrency(1234.5)).toBe('¥1234.50');
    });

    it('应该返回美元格式当指定 USD 时', () => {
      expect(formatCurrency(99.99, 'USD')).toBe('$99.99');
    });

    it('应该返回欧元格式当指定 EUR 时', () => {
      expect(formatCurrency(50, 'EUR')).toBe('€50.00');
    });

    it('应该返回原始货币符号当指定未知货币时', () => {
      expect(formatCurrency(100, 'JPY')).toBe('JPY100.00');
    });

    it('应该抛出错误当金额为负数时', () => {
      expect(() => formatCurrency(-10)).toThrow('金额不能为负数');
    });

    it('应该抛出错误当金额为 NaN 时', () => {
      expect(() => formatCurrency(NaN)).toThrow('金额必须是有效数字');
    });

    it('应该抛出错误当金额为 Infinity 时', () => {
      expect(() => formatCurrency(Infinity)).toThrow('金额必须是有效数字');
    });
  });

  describe('validateEmail', () => {
    it('应该返回 true 当邮箱格式正确时', () => {
      expect(validateEmail('user@example.com')).toBe(true);
    });

    it('应该返回 true 当邮箱包含点号和加号时', () => {
      expect(validateEmail('user.name+tag@example.co.uk')).toBe(true);
    });

    it('应该返回 false 当缺少 @ 符号时', () => {
      expect(validateEmail('userexample.com')).toBe(false);
    });

    it('应该返回 false 当缺少域名时', () => {
      expect(validateEmail('user@')).toBe(false);
    });

    it('应该返回 false 当输入为空字符串时', () => {
      expect(validateEmail('')).toBe(false);
    });

    it('应该返回 false 当输入为 null 时', () => {
      expect(validateEmail(null as any)).toBe(false);
    });

    it('应该返回 false 当输入不是字符串时', () => {
      expect(validateEmail(123 as any)).toBe(false);
    });
  });

  describe('generateSlug', () => {
    it('应该将空格替换为连字符', () => {
      expect(generateSlug('hello world')).toBe('hello-world');
    });

    it('应该去除特殊字符', () => {
      expect(generateSlug('Hello, World!')).toBe('hello-world');
    });

    it('应该转为小写', () => {
      expect(generateSlug('HELLO')).toBe('hello');
    });

    it('应该合并多个连字符为一个', () => {
      expect(generateSlug('hello   world')).toBe('hello-world');
    });

    it('应该去除首尾空格', () => {
      expect(generateSlug('  hello  ')).toBe('hello');
    });
  });

  describe('parseDate', () => {
    it('应该解析 ISO 格式日期', () => {
      const result = parseDate('2026-04-09T12:00:00Z');
      expect(result).toBeInstanceOf(Date);
      expect(result.toISOString()).toContain('2026-04-09');
    });

    it('应该解析简单日期字符串', () => {
      const result = parseDate('2026-04-09');
      expect(result.getFullYear()).toBe(2026);
      expect(result.getMonth() + 1).toBe(4);
    });

    it('应该抛出错误当输入为空时', () => {
      expect(() => parseDate('')).toThrow('日期字符串不能为空');
    });

    it('应该抛出错误当输入不是字符串时', () => {
      expect(() => parseDate(null as any)).toThrow('日期字符串不能为空');
    });

    it('应该抛出错误当日期格式无效时', () => {
      expect(() => parseDate('not-a-date')).toThrow('无效的日期格式');
    });
  });
});
