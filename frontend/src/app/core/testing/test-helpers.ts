import { Type } from '@angular/core';
import { ComponentFixture, TestBed, TestModuleMetadata } from '@angular/core/testing';
import { NoopAnimationsModule } from '@angular/platform-browser/animations';
import { RouterTestingModule } from '@angular/router/testing';
import { HttpClientTestingModule } from '@angular/common/http/testing';

// Material modules needed for testing
import { MatSnackBarModule } from '@angular/material/snack-bar';
import { MatDialogModule } from '@angular/material/dialog';

/**
 * Creates a test bed configuration with common testing modules and providers
 * @param additionalConfig Additional test module configuration
 */
export function createTestBedConfig(additionalConfig: TestModuleMetadata = {}): TestModuleMetadata {
  return {
    imports: [
      // Common testing modules
      NoopAnimationsModule,
      RouterTestingModule,
      HttpClientTestingModule,
      
      // Material modules needed for most tests
      MatSnackBarModule,
      MatDialogModule,
      
      // Additional imports from config
      ...(additionalConfig.imports || [])
    ],
    declarations: [
      ...(additionalConfig.declarations || [])
    ],
    providers: [
      ...(additionalConfig.providers || [])
    ],
    schemas: [
      ...(additionalConfig.schemas || [])
    ]
  };
}

/**
 * Creates a test component fixture with proper change detection
 * @param componentType The component to create
 * @param additionalConfig Additional test module configuration
 */
export async function createComponent<T>(
  componentType: Type<T>,
  additionalConfig: TestModuleMetadata = {}
): Promise<{ fixture: ComponentFixture<T>; component: T }> {
  await TestBed.configureTestingModule(createTestBedConfig({
    declarations: [componentType],
    ...additionalConfig
  })).compileComponents();

  const fixture = TestBed.createComponent(componentType);
  const component = fixture.componentInstance;
  fixture.detectChanges();
  
  return { fixture, component };
}

/**
 * Mocks the window object for tests that interact with browser APIs
 * @param mocks Partial window object with mocks
 */
export function mockWindow(mocks: Partial<Window>): void {
  Object.defineProperty(window, 'location', {
    value: {
      ...window.location,
      ...mocks,
      reload: jasmine.createSpy('reload')
    },
    writable: true
  });
}

/**
 * Returns a promise that resolves after the specified number of milliseconds
 * @param ms Number of milliseconds to wait
 */
export function delay(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms));
}

/**
 * Helper to create a mock object with type safety
 * @param overrides Partial object with mock values
 */
export function createMock<T>(overrides: Partial<T> = {}): T {
  return {
    ...overrides
  } as T;
}

/**
 * Helper to create a spy object with type safety
 * @param spyOn The object to spy on
 * @param method The method to spy on
 * @param returnValue The value to return when the spy is called
 */
export function createSpy<T, K extends keyof T>(
  spyOn: T,
  method: K,
  returnValue?: any
): jasmine.Spy {
  const spy = spyOn[method] as jasmine.Spy;
  if (returnValue !== undefined) {
    spy.and.returnValue(returnValue);
  }
  return spy;
}

/**
 * Helper to set input values on a form control
 * @param fixture The component fixture
 * @param selector The form control selector
 * @param value The value to set
 * @param isCheckbox Whether the input is a checkbox
 */
export function setFormControlValue(
  fixture: ComponentFixture<any>,
  selector: string,
  value: any,
  isCheckbox = false
): void {
  const input = fixture.debugElement.nativeElement.querySelector(selector);
  if (isCheckbox) {
    input.checked = value;
  } else {
    input.value = value;
  }
  input.dispatchEvent(new Event(isCheckbox ? 'change' : 'input'));
  fixture.detectChanges();
}

/**
 * Helper to dispatch a click event
 * @param fixture The component fixture
 * @param selector The element selector
 */
export function click(fixture: ComponentFixture<any>, selector: string): void {
  const element = fixture.debugElement.nativeElement.querySelector(selector);
  if (element) {
    element.click();
    fixture.detectChanges();
  } else {
    console.warn(`Element not found: ${selector}`);
  }
}

/**
 * Helper to get an element by test ID
 * @param fixture The component fixture
 * @param testId The test ID of the element
 */
export function getByTestId(fixture: ComponentFixture<any>, testId: string): HTMLElement {
  return fixture.debugElement.nativeElement.querySelector(`[data-testid="${testId}"]`);
}
