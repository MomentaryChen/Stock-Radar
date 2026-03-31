import { useMemo, useState } from "react";
import { Button, Card, Form, Input, Popconfirm, Space, Table, Tag, Typography, message } from "antd";
import type { Industry } from "../../types";
import {
  addCustomIndustry,
  deleteCustomIndustry,
  getCustomIndustries,
  stringifyTickers,
  updateCustomIndustry,
} from "../../utils/customIndustries";
import { useT } from "../../i18n";

interface IndustryConfigTabProps {
  onChanged: () => void;
}

export default function IndustryConfigTab({ onChanged }: IndustryConfigTabProps) {
  const [form] = Form.useForm();
  const [customIndustries, setCustomIndustries] = useState<Industry[]>(() => getCustomIndustries());
  const [editingName, setEditingName] = useState<string | null>(null);
  const t = useT();

  const rows = useMemo(
    () =>
      customIndustries.map((item) => ({
        key: item.name,
        name: item.name,
        tickers: item.tickers,
      })),
    [customIndustries]
  );

  const handleAdd = async () => {
    try {
      const values = await form.validateFields();
      const next = addCustomIndustry(values.name, values.tickers);
      setCustomIndustries(next);
      form.resetFields();
      message.success(t("industryConfig.addSuccess"));
      onChanged();
    } catch (error) {
      if (error instanceof Error && error.message === "Industry name already exists") {
        message.error(t("industryConfig.duplicate"));
      }
    }
  };

  const handleDelete = (name: string) => {
    const next = deleteCustomIndustry(name);
    setCustomIndustries(next);
    message.success(t("industryConfig.deleteSuccess"));
    onChanged();
  };

  const handleStartEdit = (item: Industry) => {
    setEditingName(item.name);
    form.setFieldsValue({
      name: item.name,
      tickers: stringifyTickers(item.tickers),
    });
  };

  const handleSaveEdit = async () => {
    if (!editingName) return;
    try {
      const values = await form.validateFields();
      const next = updateCustomIndustry(editingName, values.name, values.tickers);
      setCustomIndustries(next);
      setEditingName(null);
      form.resetFields();
      message.success(t("industryConfig.updateSuccess"));
      onChanged();
    } catch (error) {
      if (error instanceof Error && error.message === "Industry name already exists") {
        message.error(t("industryConfig.duplicate"));
      }
    }
  };

  const handleCancelEdit = () => {
    setEditingName(null);
    form.resetFields();
  };

  return (
    <Space direction="vertical" size={16} style={{ width: "100%" }}>
      <Card title={t("industryConfig.title")}>
        <Form form={form} layout="vertical">
          <Form.Item
            label={t("industryConfig.name")}
            name="name"
            rules={[{ required: true, message: t("industryConfig.nameRequired") }]}
          >
            <Input placeholder={t("industryConfig.namePlaceholder")} />
          </Form.Item>
          <Form.Item
            label={t("industryConfig.tickers")}
            name="tickers"
            rules={[{ required: true, message: t("industryConfig.tickersRequired") }]}
          >
            <Input placeholder={t("industryConfig.tickersPlaceholder")} />
          </Form.Item>
          <Space>
            {editingName ? (
              <>
                <Button type="primary" onClick={handleSaveEdit}>
                  {t("industryConfig.save")}
                </Button>
                <Button onClick={handleCancelEdit}>{t("industryConfig.cancelEdit")}</Button>
              </>
            ) : (
              <Button type="primary" onClick={handleAdd}>
                {t("industryConfig.add")}
              </Button>
            )}
          </Space>
        </Form>
      </Card>

      <Card title={t("industryConfig.customList")}>
        <Table
          dataSource={rows}
          pagination={false}
          locale={{ emptyText: t("industryConfig.empty") }}
          columns={[
            {
              title: t("industryConfig.columnName"),
              dataIndex: "name",
              key: "name",
            },
            {
              title: t("industryConfig.columnTickers"),
              dataIndex: "tickers",
              key: "tickers",
              render: (tickers: string[]) => (
                <Space size={[4, 4]} wrap>
                  {tickers.map((ticker) => (
                    <Tag key={ticker}>{ticker}</Tag>
                  ))}
                </Space>
              ),
            },
            {
              title: t("industryConfig.columnActions"),
              key: "actions",
              width: 180,
              render: (_, row: { name: string }) => (
                <Space>
                  <Button
                    size="small"
                    onClick={() =>
                      handleStartEdit({
                        name: row.name,
                        tickers:
                          customIndustries.find((item) => item.name === row.name)?.tickers || [],
                      })
                    }
                  >
                    {t("industryConfig.edit")}
                  </Button>
                  <Popconfirm
                    title={t("industryConfig.deleteConfirm")}
                    onConfirm={() => handleDelete(row.name)}
                    okText={t("industryConfig.confirm")}
                    cancelText={t("industryConfig.cancel")}
                  >
                    <Button danger size="small">
                      {t("industryConfig.delete")}
                    </Button>
                  </Popconfirm>
                </Space>
              ),
            },
          ]}
        />
        <Typography.Paragraph type="secondary" style={{ marginTop: 12, marginBottom: 0 }}>
          {t("industryConfig.hint")}
        </Typography.Paragraph>
      </Card>
    </Space>
  );
}
