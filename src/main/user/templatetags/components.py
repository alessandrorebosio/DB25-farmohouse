from django import template

register = template.Library()


class ListCardNode(template.Node):
    def __init__(self, title_var, items_var, empty_text_var, nodelist):
        self.title_var = template.Variable(title_var)
        self.items_var = template.Variable(items_var)
        self.empty_text_var = template.Variable(empty_text_var)
        self.nodelist = nodelist

    def render(self, context):
        try:
            title = self.title_var.resolve(context)
        except Exception:
            title = ""
        try:
            items = self.items_var.resolve(context)
        except Exception:
            items = []
        try:
            empty_text = self.empty_text_var.resolve(context)
        except Exception:
            empty_text = ""

        out = []
        out.append('<div class="col">')
        out.append('<div class="card h-100 shadow-sm rounded-4 card-hover">')
        out.append('<div class="card-body">')
        out.append(
            f'<h5 class="text-center card-title mb-3">{template.defaultfilters.force_escape(title)}</h5>'
        )

        if items:
            out.append('<ol class="list-group list-group-numbered list-group-flush">')
            for item in items:
                # Push a new context with 'item'
                context.push()
                context["item"] = item
                try:
                    out.append(self.nodelist.render(context))
                finally:
                    context.pop()
            out.append("</ol>")
        else:
            out.append(
                f'<p class="text-center text-muted small mb-0">{template.defaultfilters.force_escape(empty_text)}</p>'
            )

        out.append("</div></div></div>")
        return "".join(out)


@register.tag(name="list_card")
def do_list_card(parser, token):
    """
    Usage:
        {% list_card title=title_expr items=items_expr empty=empty_text_expr %}
          ... inline HTML using {{ item }} ...
        {% endlist_card %}
    """
    bits = token.split_contents()
    tag_name = bits[0]
    kwargs = {}
    for bit in bits[1:]:
        if "=" not in bit:
            raise template.TemplateSyntaxError(
                f"'{tag_name}' tag arguments must be key=value"
            )
        k, v = bit.split("=", 1)
        if k not in {"title", "items", "empty"}:
            raise template.TemplateSyntaxError(
                f"'{tag_name}' received unexpected argument '{k}'. Allowed: title, items, empty"
            )
        kwargs[k] = v

    missing = {"title", "items", "empty"} - set(kwargs.keys())
    if missing:
        raise template.TemplateSyntaxError(
            f"'{tag_name}' missing required args: {', '.join(sorted(missing))}"
        )

    nodelist = parser.parse(("endlist_card",))
    parser.delete_first_token()
    return ListCardNode(kwargs["title"], kwargs["items"], kwargs["empty"], nodelist)
