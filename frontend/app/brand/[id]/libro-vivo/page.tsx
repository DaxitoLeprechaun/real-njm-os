export default function LibroVivoPage({
  params,
}: {
  params: { id: string };
}) {
  return (
    <div className="p-8">
      <h1 className="text-2xl font-bold text-foreground">Libro Vivo</h1>
      <p className="text-muted-foreground mt-1 text-sm">Brand: {params.id}</p>
    </div>
  );
}
