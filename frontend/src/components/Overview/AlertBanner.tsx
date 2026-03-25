import { Alert } from "antd";
import type { TriggeredAlert } from "../../types";

interface Props {
  alerts: TriggeredAlert[];
}

export default function AlertBanner({ alerts }: Props) {
  if (!alerts.length) return null;
  return (
    <div style={{ marginBottom: 16, display: "flex", flexDirection: "column", gap: 8 }}>
      {alerts.map((a, i) => (
        <Alert
          key={i}
          message={`${a.ticker}: ${a.message}`}
          type={a.level === "success" ? "success" : "warning"}
          showIcon
        />
      ))}
    </div>
  );
}
