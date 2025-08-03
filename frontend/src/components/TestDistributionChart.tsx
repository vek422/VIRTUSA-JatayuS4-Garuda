import { ResponsivePie } from "@nivo/pie";

type InputTestDistribution = {
  type: string;
  value: string;
};
interface TestDistributionChartProps {
  data: InputTestDistribution[];
}

const getColorForType = (type: string): string => {
  switch (type) {
    case "scheduled":
      return "#2563eb"; // Blue-600
    case "draft":
      return "#f59e0b"; // Orange-500
    case "live":
      return "#a21caf"; // Purple-700
    case "ended":
      return "#22c55e"; // Green-500
    default:
      return "#8b5cf6"; // Violet-500
  }
};

export default function TestDistributionChart({
  data,
}: TestDistributionChartProps) {
  // Transform data to include colors
  const transformedData = data.map((item) => ({
    id: item.type,
    label: item.value.toString().toUpperCase(),
    value: item.value,
    color: getColorForType(item.type),
  }));
  return (
    <div className="w-full h-72">
      <ResponsivePie
        data={transformedData}
        margin={{ top: 40, right: 80, bottom: 80, left: 80 }}
        innerRadius={0.5}
        padAngle={5}
        cornerRadius={1}
        activeOuterRadiusOffset={8}
        activeInnerRadiusOffset={8}
        colors={(datum) => datum.data.color}
        borderWidth={1}
        borderColor={{
          from: "color",
          modifiers: [["darker", 0.2]],
        }}
        enableArcLabels={false}
        enableArcLinkLabels={true}
        arcLinkLabelsSkipAngle={10}
        arcLinkLabelsTextColor="#374151"
        arcLinkLabelsThickness={2}
        arcLinkLabelsColor={{ from: "color" }}
        arcLabelsSkipAngle={10}
        arcLabelsTextColor={{
          from: "color",
          modifiers: [["darker", 2]],
        }}
        animate={false}
        motionConfig="disabled"
        tooltip={({ datum }) => (
          <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-3 shadow-lg">
            <div className="flex items-center gap-2">
              <div
                className="w-3 h-3 rounded-full"
                style={{ backgroundColor: datum.color }}
              />
              <span className="font-semibold text-gray-900 dark:text-gray-100">
                {datum.label}
              </span>
            </div>
            <div className="text-blue-600 dark:text-blue-400 text-sm mt-1">
              {datum.id}
            </div>
            <div className="text-gray-500 dark:text-gray-400 text-xs">
              {(
                (Number(datum.value) /
                  data.reduce((sum, item) => sum + Number(item.value), 0)) *
                100
              ).toFixed(1)}
              %
            </div>
          </div>
        )}
      />
    </div>
  );
}
