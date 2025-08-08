import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { TestBed, fakeAsync, tick } from '@angular/core/testing';
import { RouterTestingModule } from '@angular/router/testing';
import { Router } from '@angular/router';
import { of, throwError } from 'rxjs';

import { AuthService, User } from './auth.service';
import { createSpy } from '../testing/test-helpers';

describe('AuthService', () => {
  let service: AuthService;
  let httpMock: HttpTestingController;
  let router: Router;
  
  const testUser: User = {
    id: '1',
    username: 'testuser',
    email: 'test@example.com',
    role: 'user',
    token: 'test-token'
  };

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [
        HttpClientTestingModule,
        RouterTestingModule.withRoutes([
          { path: 'login', redirectTo: '' },
          { path: 'dashboard', redirectTo: '' }
        ])
      ],
      providers: [AuthService]
    });

    service = TestBed.inject(AuthService);
    httpMock = TestBed.inject(HttpTestingController);
    router = TestBed.inject(Router);
    
    // Clear localStorage before each test
    localStorage.clear();
  });

  afterEach(() => {
    // Verify that there are no outstanding HTTP requests
    httpMock.verify();
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  describe('login', () => {
    it('should return user data and store it in localStorage on successful login', fakeAsync(() => {
      // Spy on router.navigate
      const navigateSpy = spyOn(router, 'navigate');
      
      // Call login
      service.login('testuser', 'password').subscribe(user => {
        expect(user).toEqual(testUser);
        expect(service.currentUserValue).toEqual(testUser);
        expect(localStorage.getItem('currentUser')).toBe(JSON.stringify(testUser));
      });
      
      // Expect a single request to the login endpoint
      const req = httpMock.expectOne(`${service['API_URL']}/login`);
      expect(req.request.method).toBe('POST');
      
      // Respond with mock data
      req.flush({ user: testUser, token: 'test-token' });
      
      // Wait for async operations to complete
      tick();
      
      // Verify navigation
      expect(navigateSpy).toHaveBeenCalledWith(['/dashboard']);
    }));
    
    it('should handle login error', fakeAsync(() => {
      const errorMessage = 'Invalid credentials';
      let errorResponse: any;
      
      // Call login with error
      service.login('invalid', 'credentials').subscribe({
        next: () => fail('should have failed with error'),
        error: (error) => errorResponse = error
      });
      
      // Expect a single request to the login endpoint
      const req = httpMock.expectOne(`${service['API_URL']}/login`);
      
      // Respond with error
      req.flush({ message: errorMessage }, { status: 401, statusText: 'Unauthorized' });
      
      // Wait for async operations to complete
      tick();
      
      // Verify error handling
      expect(errorResponse).toBeDefined();
      expect(errorResponse.message).toContain('Login failed');
      expect(service.currentUserValue).toBeNull();
      expect(localStorage.getItem('currentUser')).toBeNull();
    }));
  });
  
  describe('logout', () => {
    it('should clear user data and navigate to login', () => {
      // Set up initial state
      localStorage.setItem('currentUser', JSON.stringify(testUser));
      service['currentUserSubject'].next(testUser);
      
      // Spy on router.navigate
      const navigateSpy = spyOn(router, 'navigate');
      
      // Call logout
      service.logout();
      
      // Verify state after logout
      expect(service.currentUserValue).toBeNull();
      expect(localStorage.getItem('currentUser')).toBeNull();
      
      // Verify navigation
      expect(navigateSpy).toHaveBeenCalledWith(['/login']);
    });
  });
  
  describe('isAuthenticated', () => {
    it('should return true when user is authenticated', () => {
      // Set up authenticated user
      service['currentUserSubject'].next(testUser);
      
      // Verify authentication state
      expect(service.isAuthenticated()).toBeTrue();
    });
    
    it('should return false when user is not authenticated', () => {
      // Ensure no user is set
      service['currentUserSubject'].next(null);
      
      // Verify authentication state
      expect(service.isAuthenticated()).toBeFalse();
    });
  });
  
  describe('hasRole', () => {
    it('should return true when user has the specified role', () => {
      // Set up user with admin role
      const adminUser = { ...testUser, role: 'admin' };
      service['currentUserSubject'].next(adminUser);
      
      // Verify role check
      expect(service.hasRole('admin')).toBeTrue();
    });
    
    it('should return false when user does not have the specified role', () => {
      // Set up regular user
      service['currentUserSubject'].next(testUser);
      
      // Verify role check
      expect(service.hasRole('admin')).toBeFalse();
    });
    
    it('should return false when no user is authenticated', () => {
      // Ensure no user is set
      service['currentUserSubject'].next(null);
      
      // Verify role check
      expect(service.hasRole('admin')).toBeFalse();
    });
  });
  
  describe('refreshToken', () => {
    it('should refresh the token and update user data', fakeAsync(() => {
      // Set up initial user
      service['currentUserSubject'].next(testUser);
      
      // New token data
      const newToken = 'new-test-token';
      const newUserData = { ...testUser, email: 'updated@example.com' };
      
      // Call refreshToken
      service.refreshToken().subscribe(user => {
        expect(user).toEqual({ ...newUserData, token: newToken });
        expect(service.currentUserValue).toEqual({ ...newUserData, token: newToken });
        expect(localStorage.getItem('currentUser')).toBe(
          JSON.stringify({ ...newUserData, token: newToken })
        );
      });
      
      // Expect a single request to the refresh token endpoint
      const req = httpMock.expectOne(`${service['API_URL']}/refresh-token`);
      expect(req.request.method).toBe('POST');
      expect(req.request.body).toEqual({ token: testUser.token });
      
      // Respond with new token data
      req.flush({ user: newUserData, token: newToken });
      
      // Wait for async operations to complete
      tick();
    }));
    
    it('should logout on token refresh error', fakeAsync(() => {
      // Set up initial user
      service['currentUserSubject'].next(testUser);
      
      // Spy on logout
      const logoutSpy = spyOn(service, 'logout');
      
      // Call refreshToken with error
      service.refreshToken().subscribe({
        next: () => fail('should have failed with error'),
        error: (error) => {
          expect(error).toBeDefined();
        }
      });
      
      // Expect a single request to the refresh token endpoint
      const req = httpMock.expectOne(`${service['API_URL']}/refresh-token`);
      
      // Respond with error
      req.flush({ message: 'Token expired' }, { status: 401, statusText: 'Unauthorized' });
      
      // Wait for async operations to complete
      tick();
      
      // Verify logout was called
      expect(logoutSpy).toHaveBeenCalled();
    }));
    
    it('should throw error if no current user', fakeAsync(() => {
      // Ensure no user is set
      service['currentUserSubject'].next(null);
      
      // Call refreshToken
      service.refreshToken().subscribe({
        next: () => fail('should have thrown error'),
        error: (error) => {
          expect(error.message).toContain('No current user');
        }
      });
      
      // No HTTP request should be made
      httpMock.expectNone(`${service['API_URL']}/refresh-token`);
      
      // Wait for async operations to complete
      tick();
    }));
  });
});
