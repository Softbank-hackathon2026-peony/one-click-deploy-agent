import { supabase } from "@/lib/supabase";

export default async function Post({ params }: { params: { slug: string } }) {
  const { data } = await supabase.from("posts").select("*").eq("slug", params.slug).single();
  return <article>{data?.body}</article>;
}
