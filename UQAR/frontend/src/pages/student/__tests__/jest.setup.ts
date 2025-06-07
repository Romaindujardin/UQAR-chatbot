// Setup file for Jest tests
// This file adds type declarations for Jest and testing-library

declare namespace jest {
  interface Mock<T = any, Y extends any[] = any[]> extends Function {
    new (...args: Y): T;
    (...args: Y): T;
    mockImplementation(fn: (...args: Y) => T): this;
    mockImplementationOnce(fn: (...args: Y) => T): this;
    mockResolvedValue(value: Awaited<T>): this;
    mockResolvedValueOnce(value: Awaited<T>): this;
    mockRejectedValue(value: any): this;
    mockRejectedValueOnce(value: any): this;
    mockReturnValue(value: T): this;
    mockReturnValueOnce(value: T): this;
    mockReset(): void;
    mockRestore(): void;
    mockClear(): void;
    getMockName(): string;
    mockName(name: string): this;
    mockReturnThis(): this;
    mockReturnsThis(): this;
    mockRejectedThis(): this;
    mockReset(): this;
    mockRestore(): this;
    mockClear(): this;
    mockClearAll(): void;
    mockRestoreAll(): void;
    mockResetAll(): void;
    mockImplementation(fn?: Function): this;
    mockImplementationOnce(fn: Function): this;
    mock: {
      calls: Y[];
      instances: T[];
      invocationCallOrder: number[];
      results: Array<{type: string, value: any}>;
    };
  }

  function fn<T = any, Y extends any[] = any[]>(): Mock<T, Y>;
  function fn<T = any, Y extends any[] = any[]>(implementation?: (...args: Y) => T): Mock<T, Y>;
  function mock(moduleName: string, factory?: any, options?: any): void;
  function spyOn(object: any, method: string): Mock;
  function clearAllMocks(): void;
  function resetAllMocks(): void;
  function restoreAllMocks(): void;
}

declare function describe(name: string, fn: () => void): void;
declare function test(name: string, fn: (done?: () => void) => void | Promise<void>, timeout?: number): void;
declare function expect<T>(value: T): any;
declare function beforeEach(fn: () => void | Promise<void>): void;

// Module declarations for testing libraries are already defined in global.d.ts
// We don't need to redeclare them here 