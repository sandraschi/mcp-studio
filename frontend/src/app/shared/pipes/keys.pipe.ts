import { Pipe, PipeTransform } from '@angular/core';

@Pipe({
  name: 'keys',
  standalone: true
})
export class KeysPipe implements PipeTransform {
  transform(value: any, ...args: any[]): any {
    if (!value) {
      return [];
    }
    
    // Handle both objects and maps
    if (value instanceof Map) {
      return Array.from(value.keys());
    }
    
    // Handle objects
    return Object.keys(value);
  }
}
