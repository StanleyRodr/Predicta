import { AxiosError, type AxiosResponse } from "axios";

/** An Axios error as the API answers it: status plus a JSON ``detail``. */
export function apiError(status: number, detail: string): AxiosError {
  return new AxiosError(detail, "ERR_BAD_REQUEST", undefined, undefined, {
    status,
    data: { detail },
  } as AxiosResponse);
}
