import jinja2

class db_control_sql:
    def __init__(self):
        self.SQL_PRAGMA = '''
        PRAGMA foreign_keys = ON;
        '''

        self.SQL_INIT_CONTENT_TABLE = '''
            CREATE TABLE IF NOT EXISTS CONTENT_TABLE (
                content_idx INTEGER PRIMARY KEY,
                user_idx INTEGER NOT NULL,
                title TEXT NOT NULL,
                category_idx INTEGER NOT NULL,
                created_time TEXT NOT NULL,
                updated_time TEXT NOT NULL,
                content TEXT NOT NULL,
                view_count INTEGER DEFAULT 0
            )
        '''       

        self.SQL_INIT_COMMENT_TABLE = '''
            CREATE TABLE IF NOT EXISTS COMMENT_TABLE (
                comment_idx INTEGER PRIMARY KEY,
                content_idx INTEGER NOT NULL,
                user_idx INTEGER NOT NULL,
                created_time TEXT NOT NULL,
                comment TEXT NOT NULL,
                FOREIGN KEY (content_idx) REFERENCES ParentTable(content_idx) ON DELETE CASCADE
            )
        '''     

        self.SQL_INIT_USER_TABLE = '''
            CREATE TABLE IF NOT EXISTS USER_TABLE (
                user_idx INTEGER PRIMARY KEY,
                user_id TEXT NOT NULL UNIQUE,
                user_password TEXT NOT NULL,
                user_password_question TEXT NOT NULL,
                user_password_answer TEXT NOT NULL,
                created_time TEXT NOT NULL,
                previlage TEXT NOT NULL
            )
        '''

        self.SQL_INIT_IMAGE_TABLE = '''
            CREATE TABLE IF NOT EXISTS IMAGE_TABLE (
                filename TEXT PRIMARY KEY,
                content_idx int
            )
        '''

        self.SQL_INIT_LOGGING_TABLE = '''
            CREATE TABLE IF NOT EXISTS LOGGING_TABLE (
                log_idx INTEGER PRIMARY KEY,
                timekey INTEGER,
                url TEXT,
                method TEXT,
                proc_time real,
                memory_usage real,
                success boolean,
                error_message text
            )
        '''

        self.SQL_INIT_CATEGORY_TABLE = '''
            CREATE TABLE IF NOT EXISTS CATEGORY_TABLE (
                category_idx INTEGER PRIMARY KEY,
                category TEXT UNIQUE
            )
        '''

        self.SQL_PUSH_CONTENT = """
        INSERT 
        INTO CONTENT_TABLE (
            content_idx,
            user_idx,
            title,
            category_idx,
            created_time,
            updated_time,
            content,
            view_count
        )
        VALUES (
            ?,
            ?,
            ?,
            ?,
            ?,
            ?,
            ?,
            ?
        )
        """

        self.SQL_UPDATE_CONTENT = """
        UPDATE CONTENT_TABLE
        SET title = ?,
            category_idx = ?,
            updated_time = ?,
            content = ?
        WHERE 
            content_idx = ?
        """

        self.SQL_DELETE_CONTENT = jinja2.Template("""
        DELETE 
        FROM CONTENT_TABLE
        WHERE 1=1
            AND content_idx = {{content_idx}}
        """)
        

        self.SQL_MAX_CONTENT_IDX = """
        SELECT MAX(content_idx)
        FROM CONTENT_TABLE
        """
        
        self.SQL_COUNT_CONTENT = """
        SELECT COUNT(content_idx)
        FROM CONTENT_TABLE
        """    

        self.SQL_GET_CONTENT_LIST = jinja2.Template("""
        SELECT  CONTENT.content_idx, 
                CONTENT.user_idx, 
                CONTENT.title, 
                CATE.category, 
                CONTENT.created_time, 
                CONTENT.updated_time,
                CONTENT.content,
                CONTENT.view_count,
                USER.user_id 
        FROM
            (
                SELECT  content_idx, 
                        user_idx, 
                        title, 
                        category_idx, 
                        created_time, 
                        updated_time,
                        content,
                        view_count
                FROM CONTENT_TABLE                                                                                                                            
            ) AS CONTENT,
            (
                SELECT  user_idx,
                        user_id   
                FROM USER_TABLE
            ) AS USER,
            (
                SELECT category_idx, 
                       category
                FROM CATEGORY_TABLE  
                WHERE 1=1                                    
                    {% if category %}
                        AND category = "{{category}}"
                    {% endif %}                                                                       
            ) AS CATE
        WHERE 1=1
            AND CONTENT.user_idx = USER.user_idx 
            AND CONTENT.category_idx = CATE.category_idx
        ORDER BY CONTENT.created_time DESC 
        LIMIT {{limit}}
        """ )  

        self.SQL_GET_CONTENT = jinja2.Template("""
        SELECT   CONTENT.content_idx, 
                 CONTENT.user_idx, 
                 CONTENT.title, 
                 CATE.category, 
                 CONTENT.created_time,
                 CONTENT.updated_time, 
                 CONTENT.content,
                 CONTENT.view_count,
                 USER.user_id                                                                   
        FROM (
                SELECT  content_idx, 
                        user_idx, 
                        title, 
                        category_idx, 
                        created_time, 
                        updated_time,
                        content,
                        view_count
                FROM CONTENT_TABLE
                WHERE 1=1 
                    AND CONTENT_IDX = {{content_idx}}                                                                   
            ) AS CONTENT,
            (
                SELECT  user_idx,
                        user_id   
                FROM USER_TABLE                                                                                  
            ) AS USER,
            (
                SELECT category_idx,
                        category
                FROM CATEGORY_TABLE
                WHERE 1=1                                   
            ) AS CATE  
        WHERE 1=1
            AND CONTENT.user_idx = USER.user_idx 
            AND CONTENT.category_idx = CATE.category_idx                                                                                                                                           
        
        """)

        self.SQL_GET_CONTENT_VIEW_COUNT = jinja2.Template("""
        SELECT view_count
        FROM CONTENT_TABLE
        WHERE 1=1
            AND content_idx = {{content_idx}}
        """)

        self.SQL_GET_CONTENT_COUNT = jinja2.Template("""
        SELECT COUNT(CONTENT_IDX)
        FROM CONTENT_TABLE
        WHERE 1=1
            {% if category_idx %}  
               AND category_idx = "{{category_idx}}"                                      
            {% endif %}                                           
        """)

        self.SQL_UPDATE_CONTENT_VIEW_COUNT = jinja2.Template("""
        UPDATE CONTENT_TABLE
        SET view_count = view_count + 1
        WHERE 1=1
            AND content_idx = {{content_idx}}                                             
        """)

        self.SQL_GET_ALL_USER = """
        SELECT  user_idx,
                user_id,
                user_password,
                user_password_question,
                user_password_answer,
                created_time,
                previlage
        FROM USER_TABLE
        """

        self.SQL_GET_USER_WITH_USER_IDX = jinja2.Template("""
        SELECT  user_idx,
                user_id,
                user_password,
                user_password_question,
                user_password_answer,
                created_time,
                previlage
        FROM USER_TABLE
        WHERE 1=1
            AND user_idx = {{user_idx}}
        """)

        self.SQL_FIND_USER_WITH_ID = jinja2.Template("""
        SELECT user_idx,
               user_id,
               user_password,
               user_password_question,
               user_password_answer,
               created_time,
               previlage
        FROM USER_TABLE
        WHERE 1=1
            AND user_id = "{{user_id}}"
        """)

        self.SQL_FIND_USER_WITH_ID_PW = jinja2.Template("""
        SELECT user_idx,
               user_id,
               user_password,
               user_password_question,
               user_password_answer,
               created_time,
               previlage
        FROM USER_TABLE
        WHERE 1=1
            AND user_id = "{{user_id}}"  
            AND user_password = "{{user_password}}"                                              
        """)

        self.SQL_MAX_USER_IDX = """
        SELECT MAX(user_idx)
        FROM USER_TABLE
        """

        self.SQL_PUSH_USER = """
        INSERT 
        INTO USER_TABLE (
            user_idx,
            user_id,
            user_password,
            user_password_question,
            user_password_answer,
            created_time,
            previlage
        )
        VALUES (
            ?,
            ?, 
            ?, 
            ?, 
            ?,
            ?,
            ?
        )
        """

        self.SQL_GET_USER_PASSWORD_QUESTSION_WITH_USER_ID = jinja2.Template("""
        SELECT user_idx,
                user_id,
                user_password,
                user_password_question,
                user_password_answer,
                created_time,
                previlage
        FROM USER_TABLE 
        WHERE 1=1
            AND user_id = "{{user_id}}"                                                          
        """)
        
        self.SQL_CHECK_USER_ID_AND_USER_PASSWORD_ANSWER = jinja2.Template("""
        SELECT user_idx,
                user_id,
                user_password,
                user_password_question,
                user_password_answer,
                created_time,
                previlage
        FROM USER_TABLE 
        WHERE 1=1
            AND user_id = "{{user_id}}"
            AND user_password_answer = "{{user_password_answer}}"                                                         
        """)

        self.SQL_UPDATE_USER_PASSWORD = """
        UPDATE USER_TABLE
        SET user_password = ?
        WHERE 1=1
            AND user_idx = ?
        """

        self.SQL_UPDATE_USER = """
        UPDATE USER_TABLE
        SET user_id = ?,
            user_password = ?,
            user_password_question = ?,
            user_password_answer = ?
        WHERE 1=1
            AND user_idx = ?
        """

        self.SQL_GET_IMAGE_ALL = """
        SELECT filename
        FROM IMAGE_TABLE
        """

        self.SQL_FIND_IMAGE_WITH_CONTENT_IDX = jinja2.Template("""
        SELECT filename
        FROM IMAGE_TABLE
        WHERE 1=1
            AND content_idx = {{content_idx}}
        """)

        self.SQL_DELETE_IMAGE_WITH_CONTENT_IDX = jinja2.Template("""
        DELETE 
        FROM IMAGE_TABLE
        WHERE 1=1
            AND content_idx = {{content_idx}}
        """)

        self.SQL_PUSH_IMAGE = """
        INSERT
        INTO IMAGE_TABLE (
            filename,
            content_idx
        )
        VALUES (
            ?,
            ?
        )
        """

        self.SQL_GET_COMMENT = jinja2.Template("""
        SELECT comment_idx,
               content_idx,
               user_idx,
               created_time,
               comment
        FROM COMMENT_TABLE
        WHERE 1=1
            AND comment_idx = {{comment_idx}}
        """)



        self.SQL_GET_COMMENT_LIST_WITH_CONTENT_IDX = jinja2.Template("""
        SELECT comment_idx,
               content_idx,
               user_idx,
               created_time,
               comment
        FROM COMMENT_TABLE
        WHERE 1=1
            AND content_idx = {{content_idx}}
        """)

        self.SQL_GET_MAX_COMMENT_IDX = """
        SELECT max(comment_idx)
        FROM COMMENT_TABLE
        """

        self.SQL_PUSH_COMMENT = """
        INSERT
        INTO COMMENT_TABLE (
            comment_idx,
            content_idx,
            user_idx,
            created_time,
            comment
        )
        VALUES (
            ?,
            ?,
            ?,
            ?,
            ?
        )
        """

        

        self.SQL_DELETE_COMMENT = jinja2.Template("""
        DELETE 
        FROM COMMENT_TABLE
        WHERE 1=1
            AND comment_idx = {{comment_idx}}
        """)

        self.SQL_DELETE_COMMENT_WITH_CONTENT_IDX = jinja2.Template("""
        DELETE
        FROM COMMENT_TABLE
        WHERE 1=1
             AND content_idx = {{content_idx}}
        """)

        self.SQL_PUSH_LOGGING = """
        INSERT
        INTO LOGGING_TABLE (
            log_idx, 
            timekey, 
            url, 
            method, 
            proc_time, 
            memory_usage, 
            success, 
            error_message  
        )
        VALUES (
            ?,
            ?,
            ?,
            ?,
            ?,
            ?,
            ?,
            ?
        )
        """

        self.SQL_GET_LOG_INX_MAX = """
        select max(log_idx)
        from logging_table
        """

        self.SQL_DELETE_OLD_LOG = jinja2.Template("""
        DELETE 
        FROM LOGGING_TABLE
        WHERE 1=1
            AND timekey < {{timekey}}
        """)

        self.SQL_GET_CATEGORY_WITH_IDX = jinja2.Template("""
        SELECT category
        FROM CATEGORY_TABLE
        WHERE 1=1
           AND category_idx = {{category}}                                                                                                                                
        """)

        self.SQL_GET_CATEGORY_ALL = """
        SELECT category_idx, category
        FROM CATEGORY_TABLE    
        WHERE 1=1
        ORDER BY category_idx                                          
        """

        self.SQL_MAX_CATEGORY_IDX = """
        SELECT max(category_idx)
        FROM CATEGORY_TABLE
        """

        self.SQL_PUSH_CATEGORY = jinja2.Template("""
        INSERT 
        INTO CATEGORY_TABLE (
        category_idx,
        category
            ) VALUES (
        {{category_idx}},
        "{{category}}"
        )
        """)

        self.SQL_UPDATE_CATEGORY = jinja2.Template("""
        UPDATE CATEGORY_TABLE
        SET category = "{{category}}"
        WHERE category_idx = {{category_idx}}
        """)

        self.SQL_GET_CATEGORY_IDX_WITH_CATEGORY = jinja2.Template("""
        SELECT category_idx
        FROM CATEGORY_TABLE
        WHERE 1=1
           AND category = "{{category}}"
        """)