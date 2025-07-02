import toast, { ToastOptions, ToastPosition } from 'react-hot-toast';

/**
 * Toast Service - Centralized toast notification management
 * 
 * This service provides a consistent interface for showing toast notifications
 * throughout the application. It handles different types of toasts and can
 * interpret backend API responses to show appropriate messages.
 */

export interface ToastConfig extends ToastOptions {
  position?: ToastPosition;
  duration?: number;
}

export interface ApiResponse {
  is_success: boolean;
  message: string;
  code: number;
  data?: any;
  error_code?: string;
}

class ToastService {
  private defaultConfig: ToastConfig = {
    position: 'top-right',
    duration: 4000,
  };

  /**
   * Show a success toast
   */
  success(message: string, options?: ToastConfig): string {
    return toast.success(message, {
      ...this.defaultConfig,
      ...options,
    });
  }

  /**
   * Show an error toast
   */
  error(message: string, options?: ToastConfig): string {
    return toast.error(message, {
      ...this.defaultConfig,
      duration: 6000, // Errors stay longer
      ...options,
    });
  }

  /**
   * Show an info toast
   */
  info(message: string, options?: ToastConfig): string {
    return toast(message, {
      ...this.defaultConfig,
      icon: 'ℹ️',
      ...options,
    });
  }

  /**
   * Show a warning toast
   */
  warning(message: string, options?: ToastConfig): string {
    return toast(message, {
      ...this.defaultConfig,
      icon: '⚠️',
      style: {
        background: '#FEF3C7',
        color: '#92400E',
        border: '1px solid #F59E0B',
      },
      ...options,
    });
  }

  /**
   * Show a loading toast
   */
  loading(message: string, options?: ToastConfig): string {
    return toast.loading(message, {
      ...this.defaultConfig,
      ...options,
    });
  }

  /**
   * Dismiss a specific toast
   */
  dismiss(toastId?: string): void {
    toast.dismiss(toastId);
  }

  /**
   * Dismiss all toasts
   */
  dismissAll(): void {
    toast.dismiss();
  }

  /**
   * Handle API response and show appropriate toast
   * This method interprets the common backend response structure
   */
  handleApiResponse(response: ApiResponse, options?: ToastConfig): string | null {
    if (!response) {
      return this.error('No response received from server', options);
    }

    if (response.is_success) {
      if (response.message) {
        return this.success(response.message, options);
      }
      return null; // Success but no message to show
    } else {
      // Handle error response
      let errorMessage = response.message || 'An error occurred';
      
      // Add specific error code context if available
      if (response.error_code) {
        errorMessage = `${errorMessage} (${response.error_code})`;
      }

      return this.error(errorMessage, options);
    }
  }

  /**
   * Handle API error (network errors, etc.)
   */
  handleApiError(error: any, defaultMessage: string = 'An unexpected error occurred'): string {
    let message = defaultMessage;

    if (error?.response?.data?.message) {
      message = error.response.data.message;
    } else if (error?.message) {
      message = error.message;
    }

    return this.error(message);
  }

  /**
   * Show a promise toast - useful for async operations
   */
  promise<T>(
    promise: Promise<T>,
    messages: {
      loading: string;
      success: string | ((data: T) => string);
      error: string | ((error: any) => string);
    },
    options?: ToastConfig
  ): Promise<T> {
    return toast.promise(
      promise,
      messages,
      {
        ...this.defaultConfig,
        ...options,
      }
    );
  }

  /**
   * Custom toast with custom styling
   */
  custom(
    jsx: React.ReactNode,
    options?: ToastConfig
  ): string {
    return toast.custom(jsx, {
      ...this.defaultConfig,
      ...options,
    });
  }

  /**
   * Update the default configuration
   */
  setDefaultConfig(config: Partial<ToastConfig>): void {
    this.defaultConfig = { ...this.defaultConfig, ...config };
  }
}

// Export singleton instance
export const toastService = new ToastService();

// Export individual methods for convenience
export const {
  success: showSuccess,
  error: showError,
  info: showInfo,
  warning: showWarning,
  loading: showLoading,
  dismiss: dismissToast,
  dismissAll: dismissAllToasts,
  handleApiResponse,
  handleApiError,
  promise: showPromiseToast,
  custom: showCustomToast,
} = toastService;

export default toastService;
