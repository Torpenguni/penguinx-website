// Vercel Edge Function — caches latest Shorts from Torpenguin's channel
export const config = { runtime: 'edge' };

const CHANNEL_ID = process.env.YT_CHANNEL_ID;   // UCxxxx... (channel ID, not handle)
const API_KEY    = process.env.YT_API_KEY;
const MAX_RESULTS = 8;

function iso8601ToDuration(d){
  const m = d.match(/PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?/);
  const hrs = parseInt(m?.[1]||'0',10);
  const mins = parseInt(m?.[2]||'0',10);
  const secs = parseInt(m?.[3]||'0',10);
  if(hrs>0) return `${hrs}:${String(mins).padStart(2,'0')}:${String(secs).padStart(2,'0')}`;
  return `${mins}:${String(secs).padStart(2,'0')}`;
}
function formatViews(n){
  n = Number(n);
  if(n>=1e6) return (n/1e6).toFixed(1).replace(/\.0$/,'')+'M';
  if(n>=1e3) return (n/1e3).toFixed(0)+'K';
  return String(n);
}

export default async function handler(){
  if(!CHANNEL_ID || !API_KEY){
    return new Response(JSON.stringify({error:'Missing env vars'}),{status:500});
  }
  try{
    const searchUrl = `https://www.googleapis.com/youtube/v3/search?part=snippet&channelId=${CHANNEL_ID}&maxResults=50&order=date&type=video&key=${API_KEY}`;
    const search = await fetch(searchUrl).then(r=>r.json());
    const ids = (search.items||[]).map(i=>i.id.videoId).filter(Boolean).join(',');
    if(!ids) return new Response(JSON.stringify({items:[]}));

    const detailsUrl = `https://www.googleapis.com/youtube/v3/videos?part=snippet,contentDetails,statistics&id=${ids}&key=${API_KEY}`;
    const details = await fetch(detailsUrl).then(r=>r.json());

    const items = (details.items||[])
      .filter(v=>{
        const m = v.contentDetails.duration.match(/PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?/);
        const hrs = parseInt(m?.[1]||'0',10);
        const mins = parseInt(m?.[2]||'0',10);
        const secs = parseInt(m?.[3]||'0',10);
        return hrs*3600 + mins*60 + secs >= 300;
      })
      .slice(0,MAX_RESULTS)
      .map(v=>({
        id:v.id,
        title:v.snippet.title,
        thumb:v.snippet.thumbnails.maxres?.url || v.snippet.thumbnails.high?.url,
        duration:iso8601ToDuration(v.contentDetails.duration),
        views:formatViews(v.statistics.viewCount),
      }));

    return new Response(JSON.stringify({items}),{
      headers:{
        'Content-Type':'application/json',
        'Cache-Control':'public, s-maxage=3600, stale-while-revalidate=86400',
      }
    });
  }catch(err){
    return new Response(JSON.stringify({error:String(err)}),{status:500});
  }
}
