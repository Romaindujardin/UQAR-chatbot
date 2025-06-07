import React from 'react';
/// <reference path="./jest.setup.ts" />
/// <reference path="../../../../../global.d.ts" />
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import StudentDashboard from '../dashboard'; // Adjust path as necessary

// Mock next/router
jest.mock('next/router', () => ({
  useRouter: jest.fn(() => ({
    push: jest.fn(),
    query: {},
    pathname: '/student/dashboard', // Mock current path
    asPath: '/student/dashboard',
    replace: jest.fn(),
    reload: jest.fn(),
    back: jest.fn(),
    prefetch: jest.fn().mockResolvedValue(undefined), // Mock prefetch
    beforePopState: jest.fn(),
    events: {
      on: jest.fn(),
      off: jest.fn(),
      emit: jest.fn(),
    },
    isFallback: false,
    isLocaleDomain: false,
    isReady: true, // Important for some hooks like useSearchParams
    basePath: '',
  })),
}));

// Mock react-hot-toast
jest.mock('react-hot-toast', () => ({
  success: jest.fn(),
  error: jest.fn(),
}));

// Mock localStorage
const mockUser = { id: 1, full_name: 'Test Student', username: 'teststudent', role: 'STUDENT', is_active: true };
Storage.prototype.getItem = jest.fn(key => {
  if (key === 'access_token') return 'fake-token';
  if (key === 'user') return JSON.stringify(mockUser);
  return null;
});
Storage.prototype.removeItem = jest.fn();
Storage.prototype.setItem = jest.fn(); // Add setItem mock if needed by any part of the code

// Mock fetch globally
global.fetch = jest.fn();

describe('StudentDashboard', () => {
  beforeEach(() => {
    // Reset mocks before each test
    jest.clearAllMocks();
    (global.fetch as jest.Mock).mockReset();
  });

  test('displays documents for sections and handles download', async () => {
    // Arrange
    const sectionsData = [{ id: 1, name: 'Section Alpha', is_active: true, document_count: 1, created_at: '2023-01-01' }];
    const documentsData = [{ 
      id: 101, 
      original_filename: 'Test_Document_Alpha.pdf', 
      file_size: 1024, 
      document_type: 'PDF', 
      status: 'PROCESSED', 
      is_vectorized: true, 
      uploaded_at: '2023-01-02',
    }];

    // Mock fetch for /api/sections
    (global.fetch as jest.Mock).mockImplementationOnce((url: string) => {
      if (url.endsWith('/api/sections')) {
        return Promise.resolve({
          ok: true,
          json: async () => sectionsData,
        });
      }
      return Promise.reject(new Error(`Unhandled fetch call in sections mock: ${url}`));
    });

    // Mock fetch for /api/documents/section/1
    (global.fetch as jest.Mock).mockImplementationOnce((url: string) => {
      if (url.endsWith('/api/documents/section/1')) {
        return Promise.resolve({
          ok: true,
          json: async () => documentsData,
        });
      }
      return Promise.reject(new Error(`Unhandled fetch call in documents mock: ${url}`));
    });
    
    const windowOpenSpy = jest.spyOn(window, 'open').mockImplementation(jest.fn());

    // Act
    render(<StudentDashboard />);

    // Assert (Documents Displayed)
    await waitFor(() => {
      expect(screen.getByText('Section Alpha')).toBeInTheDocument();
    });

    await waitFor(() => {
      expect(screen.getByText('Test_Document_Alpha.pdf')).toBeInTheDocument();
    });

    // Act (Click Download)
    // The download button has a title like "Télécharger Test_Document_Alpha.pdf" and text content "Télécharger"
    const downloadButton = screen.getByRole('button', { name: /télécharger Test_Document_Alpha\.pdf/i });
    expect(downloadButton).toBeInTheDocument();
    fireEvent.click(downloadButton);

    // Assert (Download Called)
    await waitFor(() => {
      expect(windowOpenSpy).toHaveBeenCalledTimes(1);
    });
    expect(windowOpenSpy).toHaveBeenCalledWith('/api/documents/download/101', '_blank');
    
    // Assert toast message for download initiated
    await waitFor(() => {
        expect(require('react-hot-toast').success).toHaveBeenCalledWith('Téléchargement de Test_Document_Alpha.pdf initié...');
    });

    // Cleanup
    windowOpenSpy.mockRestore();
  });

  test('displays error message if loading documents fails', async () => {
    // Arrange
    const sectionsData = [{ id: 2, name: 'Section Beta', is_active: true, document_count: 1, created_at: '2023-01-03' }];

    (global.fetch as jest.Mock).mockImplementationOnce((url: string) => {
      if (url.endsWith('/api/sections')) {
        return Promise.resolve({
          ok: true,
          json: async () => sectionsData,
        });
      }
      return Promise.reject(new Error(`Unhandled fetch call: ${url}`));
    });
    
    // Mock fetch for /api/documents/section/2 to fail
    (global.fetch as jest.Mock).mockImplementationOnce((url: string) => {
        if (url.endsWith('/api/documents/section/2')) {
          return Promise.resolve({
            ok: false,
            status: 500, // Simulate a server error
            json: async () => ({ detail: 'Server error' }), 
          });
        }
        return Promise.reject(new Error(`Unhandled fetch call: ${url}`));
      });

    // Act
    render(<StudentDashboard />);

    // Assert
    await waitFor(() => {
      expect(screen.getByText('Section Beta')).toBeInTheDocument();
    });
    
    // Check for the error message related to document loading
    await waitFor(() => {
        expect(screen.getByText('Erreur lors du chargement des documents.')).toBeInTheDocument();
    });

    // Also check if a toast error was displayed
    await waitFor(() => {
        expect(require('react-hot-toast').error).toHaveBeenCalledWith('Erreur lors du chargement des documents pour la section 2');
    });
  });

});
