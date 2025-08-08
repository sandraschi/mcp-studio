import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { BehaviorSubject, Observable, of, throwError } from 'rxjs';
import { catchError, map, tap } from 'rxjs/operators';
import { Router } from '@angular/router';

export interface User {
  id: string;
  username: string;
  email: string;
  role: string;
  token?: string;
}

@Injectable({
  providedIn: 'root'
})
export class AuthService {
  private currentUserSubject: BehaviorSubject<User | null>;
  public currentUser$: Observable<User | null>;
  
  // Store the URL so we can redirect after logging in
  public redirectUrl: string | null = null;
  
  // Mock API URL - replace with your actual API endpoint
  private readonly API_URL = '/api/auth';

  constructor(
    private http: HttpClient,
    private router: Router
  ) {
    // Initialize with user from localStorage if available
    const storedUser = localStorage.getItem('currentUser');
    this.currentUserSubject = new BehaviorSubject<User | null>(
      storedUser ? JSON.parse(storedUser) : null
    );
    this.currentUser$ = this.currentUserSubject.asObservable();
  }

  public get currentUserValue(): User | null {
    return this.currentUserSubject.value;
  }

  public isAuthenticated(): boolean {
    return !!this.currentUserValue?.token;
  }

  public hasRole(role: string): boolean {
    return this.currentUserValue?.role === role;
  }

  public login(username: string, password: string): Observable<User> {
    // In a real app, this would be an HTTP request to your backend
    // This is a mock implementation
    return this.http.post<{ user: User; token: string }>(`${this.API_URL}/login`, { username, password })
      .pipe(
        map(response => {
          // Store user details and jwt token in local storage
          const user = {
            ...response.user,
            token: response.token
          };
          
          localStorage.setItem('currentUser', JSON.stringify(user));
          this.currentUserSubject.next(user);
          
          return user;
        }),
        catchError(error => {
          console.error('Login failed:', error);
          return throwError(() => new Error('Login failed. Please check your credentials.'));
        })
      );
  }

  public logout(): void {
    // Remove user from local storage and set current user to null
    localStorage.removeItem('currentUser');
    this.currentUserSubject.next(null);
    
    // Navigate to login page
    this.router.navigate(['/login']);
  }

  public refreshToken(): Observable<User> {
    // In a real app, this would be an HTTP request to refresh the token
    // This is a mock implementation
    if (!this.currentUserValue?.token) {
      this.logout();
      return throwError(() => new Error('No current user'));
    }
    
    return this.http.post<{ user: User; token: string }>(`${this.API_URL}/refresh-token`, {
      token: this.currentUserValue.token
    }).pipe(
      tap(response => {
        const user = {
          ...response.user,
          token: response.token
        };
        
        localStorage.setItem('currentUser', JSON.stringify(user));
        this.currentUserSubject.next(user);
      }),
      map(response => response.user),
      catchError(error => {
        console.error('Token refresh failed:', error);
        this.logout();
        return throwError(() => new Error('Session expired. Please log in again.'));
      })
    );
  }

  // Helper method to check if token is expired
  private isTokenExpired(token: string): boolean {
    try {
      const payload = JSON.parse(atob(token.split('.')[1]));
      return payload.exp < Date.now() / 1000;
    } catch (e) {
      return true;
    }
  }
}
