import { supabase } from "@/lib/supabase";

export default async function Home() {
  const { data } = await supabase.from("posts").select("slug,title").order("created_at", { ascending: false });
  return <ul>{data?.map((p) => <li key={p.slug}>{p.title}</li>)}</ul>;
}
