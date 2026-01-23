/**
 * TrueShift - API Client Export
 * 
 * Switch between mock and real client implementation here.
 */

export * from './types';

// Uncomment the implementation you want to use:

// export { api, authToken } from './client.mock';
export { api, authToken } from './client.real';
