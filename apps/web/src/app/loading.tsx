export default function Loading() {
  return (
    <div className="flex flex-col items-center justify-center gap-3 py-20">
      <div className="h-9 w-9 animate-spin rounded-full border-2 border-brand-100 border-t-brand-600" />
      <p className="text-sm text-slate-500">页面加载中...</p>
    </div>
  );
}
