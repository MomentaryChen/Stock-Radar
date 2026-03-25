import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ConfigProvider } from "antd";
import zhTW from "antd/locale/zh_TW";
import enUS from "antd/locale/en_US";
import Dashboard from "./pages/Dashboard";
import { useStore } from "./hooks/useStore";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { retry: 1, refetchOnWindowFocus: false },
  },
});

function App() {
  const language = useStore((s) => s.language);
  return (
    <QueryClientProvider client={queryClient}>
      <ConfigProvider locale={language === "en" ? enUS : zhTW}>
        <Dashboard />
      </ConfigProvider>
    </QueryClientProvider>
  );
}

export default App;
