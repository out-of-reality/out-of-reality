from odoo import _, http
from odoo.exceptions import AccessError, MissingError
from odoo.http import request

from odoo.addons.portal.controllers.portal import CustomerPortal
from odoo.addons.portal.controllers.portal import pager as portal_pager


class GameSessionCustomerPortal(CustomerPortal):
    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        if "game_sessions_count" in counters:
            values["game_sessions_count"] = (
                request.env["clinic.game.session"].search_count(
                    self._prepare_game_session_domain()
                )
                if request.env["clinic.game.session"].check_access_rights(
                    "read", raise_exception=False
                )
                else 0
            )
        return values

    def _prepare_game_session_domain(self):
        patients = request.env["res.users.link"].search(
            [("user_id", "=", request.env.user.id)]
        )
        return [("patient_id", "in", patients.mapped("patient_id.id"))]

    def _prepare_searchbar_sortings(self):
        return {
            "date": {"label": _("Newest"), "order": "session_date desc"},
        }

    @http.route(
        ["/my/game_sessions", "/my/game_sessions/page/<int:page>"],
        type="http",
        auth="user",
        website=True,
    )
    def portal_my_game_sessions(
        self, page=1, date_begin=None, date_end=None, sortby=None, **kw
    ):
        values = self._prepare_portal_layout_values()
        GameSession = request.env["clinic.game.session"]
        domain = self._prepare_game_session_domain()

        searchbar_sortings = self._prepare_searchbar_sortings()
        if not sortby:
            sortby = "date"
        order = searchbar_sortings[sortby]["order"]

        if date_begin and date_end:
            domain += [
                ("create_date", ">", date_begin),
                ("create_date", "<=", date_end),
            ]

        game_sessions_count = GameSession.search_count(domain)

        pager = portal_pager(
            url="/my/game_sessions",
            url_args={"date_begin": date_begin, "date_end": date_end, "sortby": sortby},
            total=game_sessions_count,
            page=page,
            step=self._items_per_page,
        )

        game_sessions = GameSession.search(
            domain, order=order, limit=self._items_per_page, offset=pager["offset"]
        )

        grouped_game_sessions = {}
        for session in game_sessions:
            patient_name = session.patient_id.name or "Unknown Patient"
            if patient_name not in grouped_game_sessions:
                grouped_game_sessions[patient_name] = []
            grouped_game_sessions[patient_name].append(session)

        values.update(
            {
                "date": date_begin,
                "date_end": date_end,
                "grouped_game_sessions": grouped_game_sessions,
                "page_name": "game_sessions",
                "default_url": "/my/game_sessions",
                "pager": pager,
                "searchbar_sortings": searchbar_sortings,
                "sortby": sortby,
            }
        )
        return request.render("clinic_management.portal_my_game_sessions", values)

    @http.route(
        ["/my/game_sessions/<int:session_id>"], type="http", auth="user", website=True
    )
    def portal_game_session_page(
        self, session_id, access_token=None, message=False, **kw
    ):
        try:
            session_sudo = self._document_check_access(
                "clinic.game.session", session_id, access_token=access_token
            )
        except (AccessError, MissingError):
            return request.redirect("/my")

        values = {
            "game_session": session_sudo,
        }

        history_session_key = "my_game_sessions_history"
        values = self._get_page_view_values(
            session_sudo, access_token, values, history_session_key, False
        )

        return request.render("clinic_management.game_session_portal_template", values)
