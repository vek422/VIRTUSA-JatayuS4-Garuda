import { RouterProvider } from "react-router-dom";
import { router } from "./routes";
import { Provider } from "react-redux";
import { store, persistor } from "./store";
import { PersistGate } from "redux-persist/integration/react";
import { ThemeProvider } from "./components/theme-provider";
import { useEffect } from "react";
import { Toaster } from "@/components/ui/sonner";

export default function App() {
  useEffect(() => {
    const onStorage = (event: StorageEvent) => {
      if (!event) return;
      if (event.key === "auth_token" && !event.newValue) {
        window.location.href = "/login";
      }
      if (event.key === "auth_token" && event.newValue) {
        window.location.href = "/dashboard"; // Change if needed
      }
    };
    window.addEventListener("storage", onStorage);
    return () => window.removeEventListener("storage", onStorage);
  }, []);
  return (
    <>
      <Provider store={store}>
        <PersistGate loading={<div>Loading...</div>} persistor={persistor}>
          <ThemeProvider defaultTheme="dark" storageKey="vite-ui-theme">
            <RouterProvider router={router} />
            <Toaster />
          </ThemeProvider>
        </PersistGate>
      </Provider>
    </>
  );
}
