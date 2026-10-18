import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { beforeEach, describe, expect, it } from "vitest";
import { ProtectedRoute } from "./ProtectedRoute";
import { useAuthStore } from "../../stores/authStore";

describe("ProtectedRoute", () => {
  beforeEach(() => {
    useAuthStore.setState({ token: null, user: null, isHydrated: true, isCheckingSession: false });
  });

  it("redirects anonymous users to login", () => {
    render(
      <MemoryRouter initialEntries={["/private"]}>
        <Routes>
          <Route element={<ProtectedRoute />} path="/private" />
          <Route element={<p>Login requerido</p>} path="/login" />
        </Routes>
      </MemoryRouter>,
    );

    expect(screen.getByText("Login requerido")).toBeInTheDocument();
  });
});
