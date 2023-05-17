import { writeFileSync, mkdirSync } from "fs";
import { YoutubeTranscript } from "youtube-transcript";
import { google } from "googleapis";

const youtube = google.youtube({
  version: "v3",
  auth: process.env.YOUTUBE_API_KEY,
});

export const main = async () => {

  /**
   * Todo: to grab all videos from a channel use youtube.search.list (see example below)
   */

  // const resp = await youtube.search.list({
  //   part: ["snippet"],
  //   // @wimhof1
  //   channelId: "UCxHTM1FYxeC4F7xDsBVltGg",
  //   // playlistId: "PL2WKxL9enbZT4MGROAYhU6blP27bfED0n",
  //   type: ["video"],
  //   maxResults: 50,
  //   // pageToken: "CDIQAA",
  // });

  /**
   * Example below uses a playlistId to grab all videos from a playlist
   * In this case for the Ice Man himself :-)
   */

  const resp = await youtube.playlistItems.list({
    maxResults: 50,
    playlistId: "PL2WKxL9enbZT4MGROAYhU6blP27bfED0n",
    part: ["snippet"],
  });

  const transcripts: any = await (resp?.data?.items || []).reduce(async (pacc, item) => {
    const acc = await pacc;
    const id = item.snippet?.resourceId?.videoId;
    try {
      console.log("fetching transcript for", id);
      const transcript = await YoutubeTranscript.fetchTranscript(id || "");
      return {
        ...acc,
        [id || ""]: {
          description: item.snippet?.description,
          title: item.snippet?.title,
          transcript,
          text: transcript.map((t) => t.text).join(" ").replace(/\s\s+/, " "),
        }
      }
    } catch (e) {
      console.log("error fetching transcript for", id);
      return acc;
    }
    
  }, Promise.resolve({}));

  console.log("writing transcripts");
  try { mkdirSync("./transcripts"); } catch (e) {}
  for (const id in transcripts) {
    writeFileSync(`./transcripts/${id}.json`, JSON.stringify(transcripts[id], null, 4));
  }
};

main();