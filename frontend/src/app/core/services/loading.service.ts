import { Injectable } from '@angular/core';
import { BehaviorSubject, Observable } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class LoadingService {
  private loadingSubject = new BehaviorSubject<boolean>(false);
  private loadingMap: Map<string, boolean> = new Map<string, boolean>();

  /**
   * Get the loading state as an observable
   */
  getLoadingState(): Observable<boolean> {
    return this.loadingSubject.asObservable();
  }

  /**
   * Set the loading state
   * @param isLoading Whether the application is in a loading state
   * @param url Optional URL to track loading state for specific requests
   */
  setLoading(isLoading: boolean, url?: string): void {
    // If we have a URL, track the loading state for that specific URL
    if (url) {
      if (isLoading) {
        this.loadingMap.set(url, true);
      } else {
        this.loadingMap.delete(url);
      }
    }

    // Update the loading state based on whether there are any pending requests
    const shouldBeLoading = isLoading || this.loadingMap.size > 0;
    
    // Only emit if the state has changed
    if (this.loadingSubject.value !== shouldBeLoading) {
      this.loadingSubject.next(shouldBeLoading);
    }
  }

  /**
   * Check if a specific URL is currently loading
   * @param url The URL to check
   */
  isLoadingUrl(url: string): boolean {
    return this.loadingMap.has(url);
  }

  /**
   * Clear all loading states
   */
  clearLoading(): void {
    this.loadingMap.clear();
    this.loadingSubject.next(false);
  }
}
