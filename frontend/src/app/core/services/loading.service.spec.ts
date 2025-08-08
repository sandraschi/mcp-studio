import { TestBed } from '@angular/core/testing';
import { LoadingService } from './loading.service';

describe('LoadingService', () => {
  let service: LoadingService;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(LoadingService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  it('should emit false as initial loading state', (done: DoneFn) => {
    service.getLoadingState().subscribe(isLoading => {
      expect(isLoading).toBeFalse();
      done();
    });
  });

  it('should update loading state when setLoading is called', (done: DoneFn) => {
    let callCount = 0;
    
    service.getLoadingState().subscribe(isLoading => {
      callCount++;
      
      // First call is the initial value (false)
      if (callCount === 1) {
        expect(isLoading).toBeFalse();
      } 
      // Second call is after setLoading(true)
      else if (callCount === 2) {
        expect(isLoading).toBeTrue();
      }
      // Third call is after setLoading(false)
      else if (callCount === 3) {
        expect(isLoading).toBeFalse();
        done();
      }
    });
    
    // Change loading state
    service.setLoading(true);
    service.setLoading(false);
  });

  it('should track loading state for specific URLs', () => {
    const testUrl = '/api/test';
    
    // Set loading for specific URL
    service.setLoading(true, testUrl);
    
    // Verify URL is tracked as loading
    expect(service.isLoadingUrl(testUrl)).toBeTrue();
    
    // Clear loading state for URL
    service.setLoading(false, testUrl);
    
    // Verify URL is no longer tracked
    expect(service.isLoadingUrl(testUrl)).toBeFalse();
  });

  it('should update global loading state based on URL loading states', (done: DoneFn) => {
    const url1 = '/api/endpoint1';
    const url2 = '/api/endpoint2';
    
    let loadingStates: boolean[] = [];
    
    service.getLoadingState().subscribe(isLoading => {
      loadingStates.push(isLoading);
      
      // After all operations, check the sequence of loading states
      if (loadingStates.length === 4) {
        expect(loadingStates).toEqual([false, true, true, false]);
        done();
      }
    });
    
    // Set loading for first URL
    service.setLoading(true, url1);
    
    // Set loading for second URL
    service.setLoading(true, url2);
    
    // Clear loading for first URL (should still be loading due to second URL)
    service.setLoading(false, url1);
    
    // Clear loading for second URL (should now be done loading)
    service.setLoading(false, url2);
  });

  it('should clear all loading states', () => {
    const url1 = '/api/endpoint1';
    const url2 = '/api/endpoint2';
    
    // Set multiple loading states
    service.setLoading(true, url1);
    service.setLoading(true, url2);
    
    // Verify loading states are set
    expect(service.isLoadingUrl(url1)).toBeTrue();
    expect(service.isLoadingUrl(url2)).toBeTrue();
    
    // Clear all loading states
    service.clearLoading();
    
    // Verify all loading states are cleared
    expect(service.isLoadingUrl(url1)).toBeFalse();
    expect(service.isLoadingUrl(url2)).toBeFalse();
    
    // Verify global loading state is false
    let isLoading = true;
    service.getLoadingState().subscribe(state => isLoading = state);
    expect(isLoading).toBeFalse();
  });

  it('should not emit duplicate loading states', (done: DoneFn) => {
    let callCount = 0;
    
    service.getLoadingState().subscribe(isLoading => {
      callCount++;
      
      if (callCount === 1) {
        // Initial state
        expect(isLoading).toBeFalse();
      } else if (callCount === 2) {
        // Should change to true
        expect(isLoading).toBeTrue();
      } else if (callCount === 3) {
        // Should change back to false
        expect(isLoading).toBeFalse();
        done();
      } else {
        fail('Unexpected call to loading state subscriber');
      }
    });
    
    // Set loading to true multiple times (should only emit once)
    service.setLoading(true);
    service.setLoading(true);
    service.setLoading(true);
    
    // Set loading to false (should emit once)
    service.setLoading(false);
  });
});
