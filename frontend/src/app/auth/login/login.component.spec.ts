import { ComponentFixture, TestBed, fakeAsync, tick } from '@angular/core/testing';
import { ReactiveFormsModule } from '@angular/forms';
import { RouterTestingModule } from '@angular/router/testing';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import { NoopAnimationsModule } from '@angular/platform-browser/animations';
import { Router } from '@angular/router';
import { of, throwError } from 'rxjs';

import { LoginComponent } from './login.component';
import { AuthService } from '../../core/services/auth.service';
import { createComponent, setFormControlValue, click } from '../../core/testing/test-helpers';

describe('LoginComponent', () => {
  let component: LoginComponent;
  let fixture: ComponentFixture<LoginComponent>;
  let authService: jasmine.SpyObj<AuthService>;
  let router: Router;
  
  const testUser = {
    id: '1',
    username: 'testuser',
    email: 'test@example.com',
    role: 'user',
    token: 'test-token'
  };

  beforeEach(async () => {
    // Create a spy for the AuthService
    const authServiceSpy = jasmine.createSpyObj('AuthService', ['login']);
    
    await TestBed.configureTestingModule({
      imports: [
        ReactiveFormsModule,
        RouterTestingModule,
        NoopAnimationsModule,
        MatFormFieldModule,
        MatInputModule,
        MatButtonModule,
        MatCardModule,
        MatIconModule
      ],
      declarations: [LoginComponent],
      providers: [
        { provide: AuthService, useValue: authServiceSpy }
      ]
    }).compileComponents();
    
    // Get the test dependencies
    authService = TestBed.inject(AuthService) as jasmine.SpyObj<AuthService>;
    router = TestBed.inject(Router);
    
    // Create the component
    const result = await createComponent(LoginComponent);
    fixture = result.fixture;
    component = result.component;
    
    // Set up the router spy
    spyOn(router, 'navigate');
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
  
  it('should initialize the form with empty fields', () => {
    expect(component.loginForm).toBeDefined();
    expect(component.loginForm.get('username')?.value).toBe('');
    expect(component.loginForm.get('password')?.value).toBe('');
    expect(component.loginForm.get('rememberMe')?.value).toBeFalse();
  });
  
  it('should validate required fields', () => {
    // Test empty form
    component.loginForm.patchValue({
      username: '',
      password: ''
    });
    
    expect(component.loginForm.valid).toBeFalse();
    expect(component.loginForm.get('username')?.hasError('required')).toBeTrue();
    expect(component.loginForm.get('password')?.hasError('required')).toBeTrue();
    
    // Test with values
    component.loginForm.patchValue({
      username: 'testuser',
      password: 'password123'
    });
    
    expect(component.loginForm.valid).toBeTrue();
  });
  
  it('should call authService.login on form submission with valid data', fakeAsync(() => {
    // Arrange
    const username = 'testuser';
    const password = 'password123';
    const rememberMe = true;
    
    // Set up the auth service to return a successful login
    authService.login.and.returnValue(of(testUser));
    
    // Act - Set form values
    setFormControlValue(fixture, '#username', username);
    setFormControlValue(fixture, '#password', password);
    setFormControlValue(fixture, '#rememberMe', true, true);
    
    // Submit the form
    click(fixture, 'button[type="submit"]');
    
    // Assert
    expect(authService.login).toHaveBeenCalledWith(username, password, rememberMe);
    
    // Wait for async operations to complete
    tick();
    
    // Verify navigation
    expect(router.navigate).toHaveBeenCalledWith(['/dashboard']);
  }));
  
  it('should handle login errors', fakeAsync(() => {
    // Arrange
    const errorMessage = 'Invalid credentials';
    
    // Set up the auth service to return an error
    authService.login.and.returnValue(throwError(() => ({
      error: { message: errorMessage }
    })));
    
    // Spy on console.error to verify it's called
    spyOn(console, 'error');
    
    // Act - Set form values
    setFormControlValue(fixture, '#username', 'testuser');
    setFormControlValue(fixture, '#password', 'wrongpassword');
    
    // Submit the form
    click(fixture, 'button[type="submit"]');
    
    // Wait for async operations to complete
    tick();
    
    // Assert
    expect(authService.login).toHaveBeenCalled();
    expect(component.error).toBe(errorMessage);
    expect(component.loading).toBeFalse();
    expect(console.error).toHaveBeenCalled();
    
    // Error message should be displayed in the template
    fixture.detectChanges();
    const errorElement = fixture.nativeElement.querySelector('.error-message');
    expect(errorElement.textContent).toContain(errorMessage);
  }));
  
  it('should toggle password visibility', () => {
    // Initial state should be hidden
    expect(component.hidePassword).toBeTrue();
    
    // Toggle visibility
    component.togglePasswordVisibility();
    expect(component.hidePassword).toBeFalse();
    
    // Toggle back
    component.togglePasswordVisibility();
    expect(component.hidePassword).toBeTrue();
  });
  
  it('should show loading state during login', fakeAsync(() => {
    // Arrange
    let loginResolve: any;
    authService.login.and.returnValue(new Promise(resolve => {
      loginResolve = resolve;
    }));
    
    // Act - Set form values and submit
    setFormControlValue(fixture, '#username', 'testuser');
    setFormControlValue(fixture, '#password', 'password123');
    click(fixture, 'button[type="submit"]');
    
    // Assert - Loading should be true
    expect(component.loading).toBeTrue();
    
    // Resolve the login
    loginResolve(testUser);
    tick();
    
    // Loading should be false after login completes
    expect(component.loading).toBeFalse();
  }));
  
  it('should disable the submit button when the form is invalid', () => {
    // Initially, form is invalid and button should be disabled
    const submitButton = fixture.nativeElement.querySelector('button[type="submit"]');
    expect(submitButton.disabled).toBeTrue();
    
    // Make form valid
    setFormControlValue(fixture, '#username', 'testuser');
    setFormControlValue(fixture, '#password', 'password123');
    fixture.detectChanges();
    
    // Button should be enabled
    expect(submitButton.disabled).toBeFalse();
  });
  
  it('should navigate to signup when signup link is clicked', () => {
    // Arrange
    const navigateSpy = spyOn(router, 'navigate');
    
    // Act - Click the signup link
    const signupLink = fixture.nativeElement.querySelector('a[routerLink="/signup"]');
    signupLink.click();
    
    // Assert
    expect(navigateSpy).toHaveBeenCalledWith(['/signup']);
  });
  
  it('should show validation messages for invalid fields after form submission', () => {
    // Arrange
    const form = component.loginForm;
    
    // Act - Submit the form without filling in required fields
    component.onSubmit();
    fixture.detectChanges();
    
    // Assert - Error messages should be shown for required fields
    const usernameError = fixture.nativeElement.querySelector('mat-error');
    expect(usernameError.textContent).toContain('Username is required');
    
    // Make username valid but leave password empty
    setFormControlValue(fixture, '#username', 'testuser');
    component.onSubmit();
    fixture.detectChanges();
    
    const passwordError = fixture.nativeElement.querySelector('mat-error');
    expect(passwordError.textContent).toContain('Password is required');
  });
  
  it('should handle enter key press on the form', () => {
    // Arrange
    spyOn(component, 'onSubmit');
    const form = fixture.nativeElement.querySelector('form');
    
    // Act - Dispatch enter key event
    const enterEvent = new KeyboardEvent('keyup', {
      key: 'Enter',
      code: 'Enter',
      keyCode: 13,
      which: 13,
      bubbles: true
    });
    
    // Make form valid
    setFormControlValue(fixture, '#username', 'testuser');
    setFormControlValue(fixture, '#password', 'password123');
    
    // Dispatch the event
    form.dispatchEvent(enterEvent);
    
    // Assert
    expect(component.onSubmit).toHaveBeenCalled();
  });
});
