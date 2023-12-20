Emily's Blog Page:

This project is a functional blog page website that includes admin login and other user logins. When the admin is logged in, they have the power to create, delete, view, and search blog posts. The user has the same capabilities except for creation. The platform includes three main pages:

-About: Contains a small bio about me.
-Home: The user can view all the previous blog posts.
-Create: The admin is required to log in and has the ability to create, delete, and view posts.
-The program is broken down into these:

Database Tables:

Users: Stores the username, email, and password of a user.
Posts: Stores the title, author, content, timestamps, and image of a post.
Comments: Stores the post ID and the content of the comment.
SearchLog: Stores the search query, the status, and the date it was searched.
History table: Keeps track of when a comment is created, when a post is created, when a post is deleted, and when something is searched.
@app routes:

-'/' (login)
-'/add_post' (admin)
-'/blogPosts' (otherUser)
-'/register' (register)
-'/about' (all)

The base template lays down the content for a header and footer. The header contains links to my social media and a link to email me. The search bar is also contained in the header. There are also links to the other pages of the blog page. If the "create" link is clicked, the user will be redirected to a login page and is required to log in with the admin credentials.

The footer contains information about how to contact me and other personal details.

Any user can also post comments on the individual blog posts, which will be displayed on the home page and also in the displayPost route
