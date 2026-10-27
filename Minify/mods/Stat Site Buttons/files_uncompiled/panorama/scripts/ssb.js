function goToStatSiteProfile(provider, internal = false) {
  var profileURL = `https://www.${provider}.com/players/` + $("#FriendsID").text;
  $.DispatchEvent(internal ? "BrowserGoToURL" : "ExternalBrowserGoToURL", profileURL);
}
function goToStatSiteMatch(provider, internal = false) {
  var matchURL = `https://www.${provider}.com/matches/` + $("#MatchID").text;
  $.DispatchEvent(internal ? "BrowserGoToURL" : "ExternalBrowserGoToURL", matchURL);
}

function goToStatSiteHero(site, internal = false) {
  try {
    var localPlayerID = Players.GetLocalPlayer();
    var heroName = Players.GetPlayerSelectedHero(localPlayerID);
    var heroID = Players.GetSelectedHeroID(localPlayerID);
    if (!heroName) {
      var heroEntity = Players.GetPlayerHeroEntityIndex(localPlayerID);
      if (heroEntity > 0 && Entities.IsValidEntity(heroEntity)) {
        heroName = Entities.GetUnitName(heroEntity);
      }
    }

    var heroName = $.Localize("#" + heroName);

    if (site == "d2pt") {
      var url = "https://dota2protracker.com/hero/" + encodeURIComponent(heroName.trim()) + "?section=builds";
    } else if (site == "dotabuff") {
      var url =
        "https://www.dotabuff.com/heroes/" +
        encodeURIComponent(heroName.trim().toLowerCase().replace(/'/g, "").replace(/ /g, "-"));
    } else if (site == "stratz") {
      var url = "https://stratz.com/heroes/" + heroID + "-" + encodeURIComponent(heroName.trim());
    }

    $.DispatchEvent(internal ? "BrowserGoToURL" : "ExternalBrowserGoToURL", url);
  } catch (e) {
    $.Msg("[D2PTBB] Error: " + e);
  }
}
