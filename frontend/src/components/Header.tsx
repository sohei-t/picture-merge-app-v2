interface HeaderProps {
  serverConnected: boolean;
}

export function Header({ serverConnected }: HeaderProps) {
  return (
    <header className="bg-white border-b border-gray-200 px-6 py-4">
      <div className="flex items-center justify-between max-w-7xl mx-auto">
        <h1 className="text-xl font-bold text-gray-900">
          Picture Merge App
        </h1>
        <div className="flex items-center gap-2">
          <span
            className={`inline-block w-2.5 h-2.5 rounded-full ${
              serverConnected ? "bg-green-500" : "bg-red-500"
            }`}
          />
          <span className="text-sm text-gray-600">
            {serverConnected ? "サーバー接続中" : "未接続"}
          </span>
        </div>
      </div>
    </header>
  );
}
