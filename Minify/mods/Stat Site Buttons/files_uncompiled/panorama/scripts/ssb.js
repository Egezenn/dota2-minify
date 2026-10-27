function goToStatSiteProfile(provider, internal) {
  var profileURL = `https://www.${provider}.com/players/` + $("#FriendsID").text;
  $.DispatchEvent(internal ? "BrowserGoToURL" : "ExternalBrowserGoToURL", profileURL);
}
function goToStatSiteMatch(provider, internal) {
  var matchURL = `https://www.${provider}.com/matches/` + $("#MatchID").text;
  $.DispatchEvent(internal ? "BrowserGoToURL" : "ExternalBrowserGoToURL", matchURL);
}
