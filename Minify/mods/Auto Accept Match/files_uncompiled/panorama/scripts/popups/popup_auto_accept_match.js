function AcceptMatchPopup() {
  var delay = Game.GetConvarInt("dota_replay_manager_download_simultaneous_requests");
  $.Msg("[AutoAccept] convar used dota_replay_manager_download_simultaneous_requests=" + delay);
  if (delay == 40) {
    $.Msg("[AutoAccept] auto-accept disabled");
    return;
  }
  $.Msg("[AutoAccept] Auto-accepting match in " + delay + "s");
  $.Schedule(delay, function () {
    $.DispatchEvent("DOTAPlayAcceptMatch");
  });
}
